import asyncio
import urllib.parse
import json
import re
from datetime import datetime
from typing import List, Dict, Any

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext


async def extract_date_from_result(result_element) -> str:
    """
    Extract date from search result element.

    Args:
        result_element: Playwright element representing a search result

    Returns:
        ISO formatted date string or current date if not found
    """
    try:
        # Look for date patterns in various elements with improved selectors
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

        # First try to find specific date elements
        for selector in date_selectors:
            try:
                date_element = await result_element.query_selector(selector)
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

        # If no specific date element found, search in all text content
        if not date_text:
            try:
                all_text = await result_element.inner_text()
                # Look for date patterns in the full text
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
            from datetime import timedelta

            # Parse different Korean date formats
            if re.search(r"(\d+)분\s*전", date_text):
                # Minutes ago
                return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            elif re.search(r"(\d+)시간\s*전", date_text):
                # Hours ago
                hours_match = re.search(r"(\d+)시간\s*전", date_text)
                if hours_match:
                    hours_ago = int(hours_match.group(1))
                    target_time = datetime.now() - timedelta(hours=hours_ago)
                    return target_time.strftime("%Y-%m-%dT%H:%M:%S")
            elif re.search(r"(\d+)일\s*전", date_text):
                # Days ago
                days_match = re.search(r"(\d+)일\s*전", date_text)
                if days_match:
                    days_ago = int(days_match.group(1))
                    target_date = datetime.now() - timedelta(days=days_ago)
                    return target_date.strftime("%Y-%m-%dT00:00:00")
            elif "어제" in date_text:
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime("%Y-%m-%dT00:00:00")
            elif "오늘" in date_text:
                return datetime.now().strftime("%Y-%m-%dT00:00:00")
            else:
                # Try to parse exact dates
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

    except Exception as e:
        pass

    # Default to current date if no date found
    return datetime.now().strftime("%Y-%m-%dT00:00:00")


def export_results_to_json(
    results: List[Dict[str, Any]], query: str, filename: str | None = None
) -> str:
    """
    Export search results to JSON file with the specified structure.

    Args:
        results: List of search results from crawl_naver_search_results
        query: The search query (used as 'risk' field)
        filename: Optional filename, defaults to query-based name

    Returns:
        Path to the created JSON file
    """
    if filename is None:
        # Create filename from query
        safe_query = re.sub(r"[^\w\s-]", "", query)
        safe_query = re.sub(r"[-\s]+", "_", safe_query)
        filename = f"naver_search_{safe_query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Transform results to match the expected structure
    export_data = {
        "risk": query,
        "results": [
            {
                "title": result["title"],
                "snippet": result["snippet"],
                "date": result["date"],
                "source": result["source"],
                "url": result["url"],
            }
            for result in results
        ],
    }

    # Write to JSON file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"Results exported to: {filename}")
    return filename


async def debug_naver_page_structure(
    query: str, time_filter: str | None = None
) -> None:
    """
    Debug function to analyze Naver search page structure.

    Args:
        query: Search query string
        time_filter: Time filter
    """
    # Build Naver search URL
    base_url = "https://search.naver.com/search.naver"
    params = {"where": "web", "query": query}

    if time_filter:
        params["nso"] = time_filter
        params["nso_open"] = "1"

    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    crawler = PlaywrightCrawler(
        headless=False,  # Show browser for debugging
        browser_type="chromium",
        browser_launch_options={
            "chromium_sandbox": False,
        },
        max_requests_per_crawl=1,
    )

    @crawler.router.default_handler
    async def debug_handler(context: PlaywrightCrawlingContext) -> None:
        print(f"Debugging page: {context.request.url}")

        # Wait for page to load
        await context.page.wait_for_load_state("networkidle")

        # Take a screenshot for analysis
        await context.page.screenshot(
            path=f"debug_naver_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        # Log page structure
        print("\n=== PAGE STRUCTURE ANALYSIS ===")

        # Check different result selectors
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

                    # Analyze first element
                    if elements:
                        first_elem = elements[0]
                        text_content = await first_elem.inner_text()
                        print(
                            f"  First element text (first 100 chars): {text_content[:100]}"
                        )

                        # Check for links
                        links = await first_elem.query_selector_all("a[href]")
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


async def crawl_and_export_naver_results(
    query: str, time_filter: str | None = None, filename: str | None = None
) -> str:
    """
    Crawl Naver search results and export to JSON file in one step.

    Args:
        query: Search query string
        time_filter: Time filter (e.g., 'p%3A1h' for 1 hour)
        filename: Optional filename for export

    Returns:
        Path to the created JSON file
    """
    print(f"Crawling Naver search results for: {query}")
    results = await crawl_naver_search_results(query, time_filter)

    print(f"Found {len(results)} search results")
    json_file = export_results_to_json(results, query, filename)

    return json_file


async def crawl_naver_search_results(
    query: str, time_filter: str | None = None
) -> List[Dict[str, Any]]:
    """
    Crawl Naver search results for a given query.

    Args:
        query: Search query string
        time_filter: Time filter (e.g., 'p%3A1h' for 1 hour, 'p%3A1d' for 1 day)

    Returns:
        List of dictionaries containing search result data
    """
    results = []

    # Build Naver search URL
    base_url = "https://search.naver.com/search.naver"
    params = {"where": "web", "query": query}

    if time_filter:
        params["nso"] = time_filter
        params["nso_open"] = "1"

    search_url = f"{base_url}?{urllib.parse.urlencode(params)}"

    # Configure crawler
    crawler = PlaywrightCrawler(
        headless=True,
        browser_type="chromium",
        browser_launch_options={
            "chromium_sandbox": False,
        },
        max_requests_per_crawl=1,  # Only crawl the search results page
    )

    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        context.log.info(f"Processing Naver search results for: {query}")

        # Wait for the page to load completely
        await context.page.wait_for_load_state("networkidle")

        # Extract search results - look for individual result containers
        search_results = await context.page.query_selector_all(
            "div.item, .result_wrap, .bx, .item_section"
        )

        if not search_results:
            # Fallback to more general selectors
            search_results = await context.page.query_selector_all(
                'div[class*="result"], div[class*="item"]'
            )

        for result in search_results:
            try:
                # Extract title - look for the main title link
                title_element = await result.query_selector(
                    "a.link_tit, .title_link, .api_txt_lines a, a.tit"
                )
                if not title_element:
                    title_element = await result.query_selector(
                        'a[href*="http"]'
                    )

                title = (
                    await title_element.inner_text() if title_element else None
                )

                # Extract URL - get the actual original URL
                url = None
                if title_element:
                    href = await title_element.get_attribute("href")
                    if href:
                        # Check if it's a direct URL or a Naver redirect
                        if (
                            href.startswith("http")
                            and "search.naver.com" not in href
                        ):
                            url = href
                        elif "url=" in href:
                            # Extract from Naver redirect URL
                            import urllib.parse

                            parsed = urllib.parse.parse_qs(
                                urllib.parse.urlparse(href).query
                            )
                            if "url" in parsed:
                                url = parsed["url"][0]
                        else:
                            # Try to find data-url or other attributes
                            data_url = await title_element.get_attribute(
                                "data-url"
                            )
                            if data_url:
                                url = data_url
                            else:
                                url = href  # Use as fallback

                # Extract snippet/description
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
                    else None
                )

                # Extract source - look for source domain or site name
                source_element = await result.query_selector(
                    ".source, .from, .site, .domain"
                )
                if not source_element:
                    # Try to extract from URL
                    if url:
                        try:
                            from urllib.parse import urlparse

                            domain = urlparse(url).netloc
                            source = (
                                domain.replace("www.", "") if domain else None
                            )
                        except:
                            source = None
                else:
                    source = await source_element.inner_text()

                # Extract date with improved selectors
                date = await extract_date_from_result(result)

                # Clean up the data
                if title and url:
                    result_data = {
                        "title": title.strip(),
                        "snippet": snippet.strip() if snippet else "",
                        "url": url.strip(),
                        "source": source.strip() if source else "",
                        "date": date,
                        "search_query": query,
                    }
                    results.append(result_data)
                    context.log.info(
                        f"Extracted result: {title[:50]}... -> {url[:50]}..."
                    )
                else:
                    context.log.debug(
                        f"Skipped result - missing title or URL. Title: {title}, URL: {url}"
                    )

            except Exception as e:
                context.log.warning(f"Error extracting result: {e}")
                continue

        context.log.info(f"Extracted {len(results)} search results")

        # Store the results
        await context.push_data(
            {
                "search_results": results,
                "query": query,
                "total_results": len(results),
            }
        )

    # Run the crawler
    await crawler.run([search_url])

    return results


async def crawl_naver_multiple_queries(
    queries: List[str], time_filter: str | None = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Crawl Naver search results for multiple queries.

    Args:
        queries: List of search query strings
        time_filter: Time filter for all queries

    Returns:
        Dictionary mapping queries to their search results
    """
    all_results = {}

    for query in queries:
        print(f"Crawling results for: {query}")
        results = await crawl_naver_search_results(query, time_filter)
        all_results[query] = results

        # Add delay between requests to be respectful
        await asyncio.sleep(2)

    return all_results


async def main() -> None:
    # Example usage: Crawl Naver search results and export to JSON
    query = "Google IO 2025"
    time_filter = "p%3A1h"  # Last 1 hour

    # Option 1: Debug page structure first (uncomment to run)
    # print("Running debug analysis...")
    # await debug_naver_page_structure(query, time_filter)
    # return

    # Option 2: Regular crawl and export
    print(f"Crawling Naver search results for: {query}")
    json_file = await crawl_and_export_naver_results(query, time_filter)
    print(f"Results saved to: {json_file}")

    # Alternative methods:
    # Method 2: Separate crawling and exporting
    # results = await crawl_naver_search_results(query, time_filter)
    # json_file = export_results_to_json(results, query, "custom_filename.json")

    # Method 3: Multiple queries and export each
    # queries = ["환율 변동 위험", "Python web crawling", "AI trends 2024"]
    # for query in queries:
    #     await crawl_and_export_naver_results(query, "p%3A1d")

    # Display sample of results
    print(f"\nCrawling completed. Check the JSON file for full results.")

    # Load and display sample results
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"\nExported data summary:")
            print(f"Risk/Query: {data['risk']}")
            print(f"Total results: {len(data['results'])}")

            if data["results"]:
                print(f"\nSample results:")
                for i, result in enumerate(
                    data["results"][:3], 1
                ):  # Show first 3 results
                    print(f"\n{i}. Title: {result['title']}")
                    print(f"   Source: {result['source']}")
                    print(f"   Date: {result['date']}")
                    print(f"   URL: {result['url'][:80]}...")
                    if result["snippet"]:
                        print(f"   Snippet: {result['snippet'][:100]}...")
            else:
                print(
                    "No results found. You may need to run the debug function to analyze page structure."
                )
                print("Uncomment the debug section in main() and run again.")

    except Exception as e:
        print(f"Error reading JSON file: {e}")


if __name__ == "__main__":
    asyncio.run(main())
