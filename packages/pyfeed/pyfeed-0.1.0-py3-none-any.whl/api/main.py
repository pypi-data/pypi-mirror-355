# api/main.py

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pyfeed.parser import parse
from pyfeed.merge import merge_feeds
from pyfeed.filtering import filter_items
from hashlib import sha256
from datetime import datetime, timedelta
import json

app = FastAPI(title="pyfeed API")

CACHE = {}
CACHE_TTL = timedelta(minutes=10)


def cache_key(urls):
    joined = "|".join(sorted(urls))
    return sha256(joined.encode()).hexdigest()


def get_from_cache(urls):
    key = cache_key(urls)
    entry = CACHE.get(key)
    if entry and datetime.utcnow() < entry["expires"]:
        return entry["data"]
    return None


def store_in_cache(urls, data):
    key = cache_key(urls)
    CACHE[key] = {"data": data, "expires": datetime.utcnow() + CACHE_TTL}


def remove_duplicates(items):
    seen = set()
    result = []
    for item in items:
        ident = item.guid or item.link or item.title
        if ident and ident not in seen:
            seen.add(ident)
            result.append(item)
    return result


@app.get("/feed")
def get_feed(
    url: list[str] = Query(...),
    keyword: str = Query(None),
    category: str = Query(None),
    author: str = Query(None),
    limit: int = Query(None),
    offset: int = Query(0),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
    format: str = Query("json", pattern="^(json|text|raw)$"),
    preview: int = Query(0, description="Trim description to N characters if set"),
):
    try:
        cached = get_from_cache(url)
        if cached:
            merged = cached
        else:
            feeds = [parse(u) for u in url]
            merged = merge_feeds(feeds)
            store_in_cache(url, merged)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    items = merged.items

    for item in items:
        item.source_url = (
            getattr(item, "source_url", None) or url[0] if len(url) == 1 else None
        )

    if keyword or category or author:
        items = filter_items(items, keyword=keyword, category=category, author=author)

    items = remove_duplicates(items)

    if sort == "asc":
        items = sorted(items, key=lambda i: i.pub_date or "")
    else:
        items = sorted(items, key=lambda i: i.pub_date or "", reverse=True)

    if offset:
        items = items[offset:]

    if limit:
        items = items[:limit]

    if preview:
        for item in items:
            if item.description:
                item.description = item.description.strip()[:preview] + "..."

    merged.items = items

    last_updated = max((i.pub_date for i in items if i.pub_date), default=None)

    if format == "json":
        return {
            "status": "ok",
            "last_updated": last_updated.isoformat() if last_updated else None,
            **merged.to_dict(),
        }
    elif format == "raw":
        raw_items = [i.__dict__ for i in merged.items]
        return {"status": "ok", "items": raw_items}
    elif format == "text":
        lines = [f"{i.title} — {i.link}" for i in merged.items]
        return PlainTextResponse("\n".join(lines))

    return JSONResponse({"status": "ok", "items": []})


@app.post("/merge")
async def post_merge(request: Request):
    try:
        body = await request.json()
        urls = body.get("urls", [])
        if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
            raise ValueError("Invalid 'urls' list")
        feeds = [parse(u) for u in urls]
        merged = merge_feeds(feeds)
        return {"status": "ok", **merged.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/meta")
def get_meta(url: str = Query(...)):
    try:
        feed = parse(url)
        return {
            "status": "ok",
            "title": feed.title,
            "link": feed.link,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
