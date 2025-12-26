"""
Naver Search Crawler Module

A comprehensive module for crawling Naver search results with support for
various time filters, JSON export, and debugging capabilities.

Usage:
    from naver_search_crawler import NaverSearchCrawler

    crawler = NaverSearchCrawler()
    results = await crawler.search("your query", time_filter="p%3A1h")
    crawler.export_to_json(results, "your query", "output.json")
"""

import asyncio
import urllib.parse
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


class NaverSearchResult:
    """Data class for individual search results."""

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str = "",
        source: str = "",
        date: str = "",
        search_query: str = "",
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.date = date
        self.search_query = search_query

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format."""
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "source": self.source,
            "date": self.date,
            "search_query": self.search_query,
        }


class NaverSearchCrawler:
    """
    Main crawler class for Naver search results.

    Features:
    - Search with time filters
    - Extract titles, URLs, snippets, sources, and dates
    - Export to JSON format
    - Debug page structure
    """

    def __init__(self, headless: bool = True, max_requests: int = 1):
        """
        Initialize the crawler.

        Args:
            headless: Whether to run browser in headless mode
            max_requests: Maximum number of requests per crawl session
        """
        self.headless = headless
        self.max_requests = max_requests
        self.base_url = "https://search.naver.com/search.naver"

        # Time filter constants
        self.TIME_FILTERS = {
            "1h": "p%3A1h",
            "1d": "p%3A1d",
            "1w": "p%3A1w",
            "1m": "p%3A1m",
            "3m": "p%3A3m",
            "6m": "p%3A6m",
            "1y": "p%3A1y",
        }

    def _build_search_url(
        self, query: str, time_filter: Optional[str] = None
    ) -> str:
        """
        Build Naver search URL with parameters.

        Args:
            query: Search query string
            time_filter: Time filter parameter

        Returns:
            Complete search URL
        """
        params = {"where": "web", "query": query}

        if time_filter:
            # Convert friendly names to actual filters
            if time_filter in self.TIME_FILTERS:
                time_filter = self.TIME_FILTERS[time_filter]

            params["nso"] = time_filter
            params["nso_open"] = "1"

        return f"{self.base_url}?{urllib.parse.urlencode(params)}"

    async def _extract_date_from_element(self, result_element) -> str:
        """
        Extract date from search result element.

        Args:
            result_element: Playwright element representing a search result

        Returns:
            ISO formatted date string
        """
        try:
            # Date selectors for Naver
            date_selectors = [
                ".sub_time",
                ".time",
                ".date",
                ".datetime",
                '.sub_txt:has-text("전")',
                '.sub_txt:has-text("일")',
                '.sub_txt:has-text("월")',
                '.sub_txt:has-text("년")',
                '[class*="time"]',
                '[class*="date"]',
                ".txt_inline",
            ]

            date_text = ""

            # Find specific date elements
            for selector in date_selectors:
                try:
                    date_element = await result_element.query_selector(
                        selector
                    )
                    if date_element:
                        text = await date_element.inner_text()
                        if text and any(
                            keyword in text
                            for keyword in [
                                "전",
                                "일",
                                "월",
                                "년",
                                "시간",
                                "분",
                                "2024",
                                "2023",
                            ]
                        ):
                            date_text = text.strip()
                            break
                except:
                    continue

            # Search in all text if no specific date element found
            if not date_text:
                try:
                    all_text = await result_element.inner_text()
                    date_patterns = [
                        r"(\d{4})\.(\d{1,2})\.(\d{1,2})",  # 2024.03.11
                        r"(\d{4})-(\d{1,2})-(\d{1,2})",  # 2024-03-11
                        r"(\d{1,2})월\s*(\d{1,2})일",  # 3월 11일
                        r"(\d+)시간\s*전",  # N시간 전
                        r"(\d+)일\s*전",  # N일 전
                        r"(\d+)분\s*전",  # N분 전
                    ]

                    for pattern in date_patterns:
                        match = re.search(pattern, all_text)
                        if match:
                            date_text = match.group(0)
                            break
                except:
                    pass

            # Parse the found date text
            if date_text:
                return self._parse_korean_date(date_text)

        except Exception:
            pass

        # Default to current date
        return datetime.now().strftime("%Y-%m-%dT00:00:00")

    def _parse_korean_date(self, date_text: str) -> str:
        """
        Parse Korean date formats to ISO format.

        Args:
            date_text: Korean date text

        Returns:
            ISO formatted date string
        """
        try:
            # Minutes ago
            if re.search(r"(\d+)분\s*전", date_text):
                return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

            # Hours ago
            elif re.search(r"(\d+)시간\s*전", date_text):
                hours_match = re.search(r"(\d+)시간\s*전", date_text)
                if hours_match:
                    hours_ago = int(hours_match.group(1))
                    target_time = datetime.now() - timedelta(hours=hours_ago)
                    return target_time.strftime("%Y-%m-%dT%H:%M:%S")

            # Days ago
            elif re.search(r"(\d+)일\s*전", date_text):
                days_match = re.search(r"(\d+)일\s*전", date_text)
                if days_match:
                    days_ago = int(days_match.group(1))
                    target_date = datetime.now() - timedelta(days=days_ago)
                    return target_date.strftime("%Y-%m-%dT00:00:00")

            # Yesterday/Today
            elif "어제" in date_text:
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime("%Y-%m-%dT00:00:00")
            elif "오늘" in date_text:
                return datetime.now().strftime("%Y-%m-%dT00:00:00")

            # Exact dates
            else:
                year_match = re.search(
                    r"(\d{4})[-.](\d{1,2})[-.](\d{1,2})", date_text
                )
                if year_match:
                    year, month, day = year_match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00"

                month_day_match = re.search(
                    r"(\d{1,2})월\s*(\d{1,2})일", date_text
                )
                if month_day_match:
                    month, day = month_day_match.groups()
                    current_year = datetime.now().year
                    return f"{current_year}-{month.zfill(2)}-{day.zfill(2)}T00:00:00"

        except Exception:
            pass

        return datetime.now().strftime("%Y-%m-%dT00:00:00")

    async def _extract_original_url(self, title_element) -> Optional[str]:
        """
        Extract the original content URL from title element.

        Args:
            title_element: Playwright element containing the link

        Returns:
            Original URL or None if not found
        """
        try:
            href = await title_element.get_attribute("href")
            if not href:
                return None

            # Direct URL (not Naver redirect)
            if href.startswith("http") and "search.naver.com" not in href:
                return href

            # Extract from Naver redirect URL
            elif "url=" in href:
                parsed = urllib.parse.parse_qs(
                    urllib.parse.urlparse(href).query
                )
                if "url" in parsed:
                    return parsed["url"][0]

            # Try data-url attribute
            else:
                data_url = await title_element.get_attribute("data-url")
                if data_url:
                    return data_url
                return href  # Use as fallback

        except Exception:
            return None

    async def _extract_source_from_url(self, url: str) -> str:
        """
        Extract source domain from URL.

        Args:
            url: The URL to extract domain from

        Returns:
            Domain name or empty string
        """
        try:
            domain = urllib.parse.urlparse(url).netloc
            return domain.replace("www.", "") if domain else ""
        except:
            return ""

    async def search(
        self, query: str, time_filter: Optional[str] = None
    ) -> List[NaverSearchResult]:
        """
        Search Naver and return results.

        Args:
            query: Search query string
            time_filter: Time filter ('1h', '1d', '1w', '1m', etc.)

        Returns:
            List of NaverSearchResult objects
        """
        results = []
        search_url = self._build_search_url(query, time_filter)

        crawler = PlaywrightCrawler(
            headless=self.headless,
            browser_type="chromium",
            browser_launch_options={"chromium_sandbox": False},
            max_requests_per_crawl=self.max_requests,
        )

        @crawler.router.default_handler
        async def request_handler(context: PlaywrightCrawlingContext) -> None:
            context.log.info(f"Processing Naver search for: {query}")

            await context.page.wait_for_load_state("networkidle")

            # Find search result containers
            search_results = await context.page.query_selector_all(
                "div.item, .result_wrap, .bx, .item_section"
            )

            if not search_results:
                search_results = await context.page.query_selector_all(
                    'div[class*="result"], div[class*="item"]'
                )

            for result in search_results:
                try:
                    # Extract title and URL
                    title_element = await result.query_selector(
                        "a.link_tit, .title_link, .api_txt_lines a, a.tit"
                    )
                    if not title_element:
                        title_element = await result.query_selector(
                            'a[href*="http"]'
                        )

                    if not title_element:
                        continue

                    title = await title_element.inner_text()
                    url = await self._extract_original_url(title_element)

                    if not title or not url:
                        continue

                    # Extract snippet
                    snippet_element = await result.query_selector(
                        ".api_txt_lines:not(.total_tit), .desc, .txt, .cont"
                    )
                    if not snippet_element:
                        snippet_element = await result.query_selector(
                            "span, p, div"
                        )
                    snippet = (
                        await snippet_element.inner_text()
                        if snippet_element
                        else ""
                    )

                    # Extract source
                    source_element = await result.query_selector(
                        ".source, .from, .site, .domain"
                    )
                    if source_element:
                        source = await source_element.inner_text()
                    else:
                        source = await self._extract_source_from_url(url)

                    # Extract date
                    date = await self._extract_date_from_element(result)

                    # Create result object
                    search_result = NaverSearchResult(
                        title=title.strip(),
                        url=url.strip(),
                        snippet=snippet.strip(),
                        source=source.strip(),
                        date=date,
                        search_query=query,
                    )

                    results.append(search_result)
                    context.log.info(
                        f"Extracted: {title[:50]}... -> {url[:50]}..."
                    )

                except Exception as e:
                    context.log.warning(f"Error extracting result: {e}")
                    continue

            context.log.info(f"Total results extracted: {len(results)}")
            await context.push_data(
                {"results": [r.to_dict() for r in results]}
            )

        await crawler.run([search_url])
        return results

    def export_to_json(
        self,
        results: List[NaverSearchResult],
        query: str,
        filename: Optional[str] = None,
        output_dir: str = ".",
    ) -> str:
        """
        Export search results to JSON file.

        Args:
            results: List of search results
            query: The search query (used as 'risk' field)
            filename: Optional filename
            output_dir: Output directory

        Returns:
            Path to the created JSON file
        """
        if filename is None:
            safe_query = re.sub(r"[^\w\s-]", "", query)
            safe_query = re.sub(r"[-\s]+", "_", safe_query)
            filename = f"naver_search_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_path = Path(output_dir) / filename

        export_data = {
            "risk": query,
            "results": [
                {
                    "title": result.title,
                    "snippet": result.snippet,
                    "date": result.date,
                    "source": result.source,
                    "url": result.url,
                }
                for result in results
            ],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return str(output_path)

    async def search_and_export(
        self,
        query: str,
        time_filter: Optional[str] = None,
        filename: Optional[str] = None,
        output_dir: str = ".",
    ) -> str:
        """
        Search and export results in one step.

        Args:
            query: Search query
            time_filter: Time filter
            filename: Optional filename
            output_dir: Output directory

        Returns:
            Path to the created JSON file
        """
        results = await self.search(query, time_filter)
        return self.export_to_json(results, query, filename, output_dir)

    async def debug_page_structure(
        self, query: str, time_filter: Optional[str] = None
    ) -> None:
        """
        Debug function to analyze Naver search page structure.

        Args:
            query: Search query
            time_filter: Time filter
        """
        search_url = self._build_search_url(query, time_filter)

        crawler = PlaywrightCrawler(
            headless=False,  # Show browser for debugging
            browser_type="chromium",
            browser_launch_options={"chromium_sandbox": False},
            max_requests_per_crawl=1,
        )

        @crawler.router.default_handler
        async def debug_handler(context: PlaywrightCrawlingContext) -> None:
            print(f"Debugging page: {context.request.url}")

            await context.page.wait_for_load_state("networkidle")

            # Take screenshot
            screenshot_path = (
                f"debug_naver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            await context.page.screenshot(path=screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

            print("\n=== PAGE STRUCTURE ANALYSIS ===")

            selectors_to_try = [
                "div.item",
                ".result_wrap",
                ".bx",
                ".item_section",
                'div[class*="result"]',
                'div[class*="item"]',
                ".lst_total > li",
                ".result",
                ".search_result",
                "[data-cr-area]",
                ".api_ani_send",
            ]

            for selector in selectors_to_try:
                try:
                    elements = await context.page.query_selector_all(selector)
                    if elements:
                        print(
                            f"Found {len(elements)} elements with selector: {selector}"
                        )

                        if elements:
                            first_elem = elements[0]
                            text_content = await first_elem.inner_text()
                            print(
                                f"  First element text: {text_content[:100]}"
                            )

                            links = await first_elem.query_selector_all(
                                "a[href]"
                            )
                            if links and len(links) > 0:
                                first_link = links[0]
                                href = await first_link.get_attribute("href")
                                link_text = await first_link.inner_text()
                                href_str = href if href else "No href"
                                link_text_str = (
                                    link_text if link_text else "No text"
                                )
                                print(
                                    f"  First link: {link_text_str[:50]} -> {href_str[:100]}"
                                )
                except Exception as e:
                    print(f"Error with selector {selector}: {e}")

            print("\n=== END DEBUG ===")

        await crawler.run([search_url])

    async def batch_search(
        self,
        queries: List[str],
        time_filter: Optional[str] = None,
        output_dir: str = ".",
        delay: float = 2.0,
    ) -> Dict[str, str]:
        """
        Search multiple queries and export each to JSON.

        Args:
            queries: List of search queries
            time_filter: Time filter for all queries
            output_dir: Output directory
            delay: Delay between requests (seconds)

        Returns:
            Dictionary mapping queries to their JSON file paths
        """
        results = {}

        for query in queries:
            print(f"Processing query: {query}")
            json_file = await self.search_and_export(
                query, time_filter, output_dir=output_dir
            )
            results[query] = json_file
            print(f"Saved: {json_file}")

            # Respectful delay between requests
            if delay > 0:
                await asyncio.sleep(delay)

        return results


# CLI Interface
async def main():
    """Example usage and CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Naver Search Crawler")
    parser.add_argument("query", help="Search query")
    parser.add_argument(
        "--time-filter", "-t", help="Time filter (1h, 1d, 1w, 1m, etc.)"
    )
    parser.add_argument("--output", "-o", help="Output filename")
    parser.add_argument(
        "--output-dir", "-d", default=".", help="Output directory"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run in debug mode"
    )
    parser.add_argument(
        "--headless", action="store_true", default=True, help="Run headless"
    )

    args = parser.parse_args()

    crawler = NaverSearchCrawler(headless=args.headless)

    if args.debug:
        await crawler.debug_page_structure(args.query, args.time_filter)
    else:
        json_file = await crawler.search_and_export(
            args.query, args.time_filter, args.output, args.output_dir
        )
        print(f"Results exported to: {json_file}")


if __name__ == "__main__":
    asyncio.run(main())
