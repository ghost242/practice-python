# Naver Search Crawler Module

A comprehensive Python module for crawling Naver search results with support for various time filters, JSON export, and debugging capabilities.

## Features

- ✅ **Real URL Extraction**: Gets actual original content URLs (not Naver redirects)
- ✅ **Date Parsing**: Extracts and parses Korean date formats (`2024.03.11`, `1시간 전`, etc.)
- ✅ **Time Filtering**: Support for various time filters (1h, 1d, 1w, 1m, etc.)
- ✅ **JSON Export**: Exports results in structured JSON format
- ✅ **Batch Processing**: Search multiple queries efficiently
- ✅ **Debug Mode**: Analyze page structure for troubleshooting
- ✅ **CLI Interface**: Command-line interface for quick searches

## Installation

1. Install required dependencies:
```bash
pip install crawlee playwright
playwright install chromium
```

2. Import the module:
```python
from practice_files import NaverSearchCrawler
```

## Quick Start

### Basic Search
```python
import asyncio
from practice_files import NaverSearchCrawler

async def main():
    crawler = NaverSearchCrawler()
    
    # Search and get results
    results = await crawler.search("Google IO 2025", time_filter="1h")
    
    # Print results
    for result in results:
        print(f"Title: {result.title}")
        print(f"URL: {result.url}")
        print(f"Source: {result.source}")
        print(f"Date: {result.date}")
        print("---")

asyncio.run(main())
```

### Search and Export to JSON
```python
async def search_and_export():
    crawler = NaverSearchCrawler()
    
    # Search and export in one step
    json_file = await crawler.search_and_export(
        "환율 변동 위험", 
        time_filter="1d",
        output_dir="./results"
    )
    
    print(f"Results saved to: {json_file}")
```

## API Reference

### NaverSearchCrawler

#### Constructor
```python
NaverSearchCrawler(headless=True, max_requests=1)
```

- `headless` (bool): Run browser in headless mode
- `max_requests` (int): Maximum requests per crawl session

#### Methods

##### `search(query, time_filter=None)`
Search Naver and return results.

**Parameters:**
- `query` (str): Search query string
- `time_filter` (str, optional): Time filter ('1h', '1d', '1w', '1m', etc.)

**Returns:** List of `NaverSearchResult` objects

##### `search_and_export(query, time_filter=None, filename=None, output_dir=".")`
Search and export results to JSON in one step.

**Returns:** Path to the created JSON file

##### `export_to_json(results, query, filename=None, output_dir=".")`
Export search results to JSON file.

##### `batch_search(queries, time_filter=None, output_dir=".", delay=2.0)`
Search multiple queries and export each to JSON.

##### `debug_page_structure(query, time_filter=None)`
Debug function to analyze Naver search page structure.

### NaverSearchResult

Data class for individual search results.

**Attributes:**
- `title` (str): Article title
- `url` (str): Original content URL
- `snippet` (str): Article snippet/description
- `source` (str): Source domain/publication
- `date` (str): Publication date (ISO format)
- `search_query` (str): Original search query

## Time Filters

| Filter | Description | Naver Parameter |
|--------|-------------|-----------------|
| `"1h"` | Last 1 hour | `p%3A1h` |
| `"1d"` | Last 1 day | `p%3A1d` |
| `"1w"` | Last 1 week | `p%3A1w` |
| `"1m"` | Last 1 month | `p%3A1m` |
| `"3m"` | Last 3 months | `p%3A3m` |
| `"6m"` | Last 6 months | `p%3A6m` |
| `"1y"` | Last 1 year | `p%3A1y` |

## JSON Output Format

```json
{
  "risk": "환율 변동 위험",
  "results": [
    {
      "title": "산업연 \"원화가치 10% 하락하면 제조기업 영업이익률 0.46 ...",
      "snippet": "제조업 내 산업군을 기계장비, 소재부품, 정보통신기술(ICT)로 재분류해...",
      "date": "2024-03-11T00:00:00",
      "source": "연합뉴스",
      "url": "https://www.yna.co.kr/view/AKR20240311044400003"
    }
  ]
}
```

## Command Line Interface

```bash
# Basic search
python -m practice_files.naver_search_crawler "Google IO 2025"

# With time filter
python -m practice_files.naver_search_crawler "환율 변동 위험" --time-filter 1d

# Custom output
python -m practice_files.naver_search_crawler "AI trends" -t 1w -o results.json -d ./output

# Debug mode
python -m practice_files.naver_search_crawler "Python" --debug --headless false
```

## Examples

See `example_usage.py` for comprehensive examples including:

- Basic search and results processing
- Batch processing multiple queries
- Custom time filters
- Advanced configuration options
- Debug mode usage

## Error Handling

The module includes comprehensive error handling for:
- Network timeouts
- Missing page elements
- Invalid URLs
- Date parsing errors
- File I/O operations

## Best Practices

1. **Rate Limiting**: Use delays between requests when batch processing
2. **Error Recovery**: Handle network errors gracefully
3. **Debug Mode**: Use debug mode when selectors need updating
4. **Resource Management**: Use context managers for file operations

## Troubleshooting

### No Results Found
1. Run debug mode to analyze page structure
2. Check if Naver has changed their HTML structure
3. Verify search query and time filters

### Incorrect URLs
1. Check if Naver is using new redirect patterns
2. Update URL extraction logic if needed

### Date Parsing Issues
1. Verify Korean date formats haven't changed
2. Add new date patterns to the parser

## Contributing

When contributing to this module:

1. Test with various search queries
2. Verify URL extraction accuracy
3. Check date parsing for edge cases
4. Update documentation as needed

## License

This module is for educational and research purposes. 