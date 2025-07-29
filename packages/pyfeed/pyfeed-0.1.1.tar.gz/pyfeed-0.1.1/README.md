# pyfeed

**pyfeed** is a pure-Python RSS/Atom feed parser and backend service. It fetches, merges, filters, and normalizes feeds into clean JSON for use in frontend applications—ideal for web UIs, dashboards, or minimalist aggregators.

---

## Features

- **RSS 2.0 and Atom 1.0 parsing**
- **JSON output with clean field normalization**
- **FastAPI backend with `/feed`, `/merge`, and `/meta` endpoints**
- **Multiple URL support with feed merging**
- **Duplicate item removal**
- **Filtering by keyword, category, and author**
- **Sorting (ascending or descending by publish date)**
- **Output limit and offset (for pagination)**
- **Preview mode: truncate long descriptions**
- **Per-item `source_url` tracking**
- **`last_updated` field in responses**
- **In-memory caching for performance**
- **CLI interface for quick local parsing**

---

## Installation

```bash
git clone https://github.com/jknndy/pyfeed
cd pyfeed
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API Usage
#### `GET /feed`

Fetch, merge, and filter one or more feeds.

Query parameters:

    url: one or more feed URLs

    keyword: filter by keyword in title or description

    category: filter by category

    author: filter by author

    limit: number of items to return

    offset: skip N items

    sort: asc or desc (default: desc)

    format: json (default), text, or raw

    preview: truncate description to N characters

Example:
```
curl "http://localhost:8000/feed?url=https://xkcd.com/rss.xml&limit=5&format=json"
```
#### `POST /merge`

Merge a list of feeds and return the result.
```
{
  "urls": ["https://xkcd.com/rss.xml", "https://hnrss.org/frontpage"]
}
```
#### `GET /meta`

Fetch basic metadata from a feed.

Example:
```
curl "http://localhost:8000/meta?url=https://xkcd.com/rss.xml"
Returns:
{
  "status": "ok",
  "title": "xkcd.com",
  "link": "https://xkcd.com/"
}
```

## CLI Usage
```python
python -m pyfeed.cli https://xkcd.com/rss.xml --json --limit 3
```

## Testing
```python
pytest tests
```