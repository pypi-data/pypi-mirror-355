from pyfeed.feed import Feed, FeedItem
from datetime import datetime
import json

def test_feed_to_dict_jsonable():
    feed = Feed("T", "http://", "D", [
        FeedItem("Title", "http://x", "Desc", datetime(2024, 1, 1), guid="g", author="a", category="c", enclosure="e")
    ])
    obj = feed.to_dict()
    js = json.dumps(obj)
    assert "Title" in js
    assert "2024-01-01T00:00:00" in js
