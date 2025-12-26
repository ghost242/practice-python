"""
Example usage of the Naver Search Crawler module.

This file demonstrates various ways to use the NaverSearchCrawler
for different search scenarios.
"""

import asyncio
from .naver_search_crawler import NaverSearchCrawler


async def basic_search_example():
    """Basic search example."""
    print("=== Basic Search Example ===")

    # Create crawler instance
    crawler = NaverSearchCrawler(headless=True)

    # Search for a query
    query = "Google IO 2025"
    results = await crawler.search(query, time_filter="1h")

    print(f"Found {len(results)} results for '{query}':")
    for i, result in enumerate(results[:3], 1):  # Show first 3 results
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Source: {result.source}")
        print(f"   Date: {result.date}")
        if result.snippet:
            print(f"   Snippet: {result.snippet[:100]}...")


async def search_and_export_example():
    """Search and export to JSON example."""
    print("\n=== Search and Export Example ===")

    crawler = NaverSearchCrawler()

    # Search and export in one step
    query = "환율 변동 위험"
    json_file = await crawler.search_and_export(
        query, time_filter="1d", output_dir="./results"
    )

    print(f"Results exported to: {json_file}")


async def batch_search_example():
    """Batch search multiple queries."""
    print("\n=== Batch Search Example ===")

    crawler = NaverSearchCrawler()

    # Multiple queries
    queries = ["환율 변동 위험", "투자 리스크 관리", "경제 전망 2024"]

    results = await crawler.batch_search(
        queries,
        time_filter="1w",
        output_dir="./batch_results",
        delay=1.0,  # 1 second delay between requests
    )

    print("Batch search completed:")
    for query, file_path in results.items():
        print(f"  {query} -> {file_path}")


async def debug_example():
    """Debug page structure example."""
    print("\n=== Debug Example ===")

    crawler = NaverSearchCrawler(headless=False)  # Show browser

    # Debug the page structure
    await crawler.debug_page_structure("Google IO 2025", "1h")


async def custom_time_filters_example():
    """Demonstrate different time filters."""
    print("\n=== Time Filters Example ===")

    crawler = NaverSearchCrawler()

    query = "AI trends"
    time_filters = ["1h", "1d", "1w", "1m"]

    for time_filter in time_filters:
        results = await crawler.search(query, time_filter)
        print(f"Time filter '{time_filter}': {len(results)} results")


async def advanced_usage_example():
    """Advanced usage with custom configuration."""
    print("\n=== Advanced Usage Example ===")

    # Custom crawler configuration
    crawler = NaverSearchCrawler(
        headless=True, max_requests=5  # Allow multiple pages if needed
    )

    # Search with raw time filter
    results = await crawler.search(
        "Python web crawling",
        time_filter="p%3A1d",  # Raw Naver time filter format
    )

    print(f"Advanced search found {len(results)} results")

    # Export with custom filename
    json_file = crawler.export_to_json(
        results,
        "Python web crawling",
        filename="python_crawling_results.json",
        output_dir="./advanced_results",
    )

    print(f"Results saved to: {json_file}")


async def main():
    """Run all examples."""
    try:
        await basic_search_example()
        await search_and_export_example()
        await custom_time_filters_example()
        await advanced_usage_example()

        # Uncomment to run batch search and debug examples
        # await batch_search_example()
        # await debug_example()

        print("\n=== All examples completed successfully! ===")

    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
