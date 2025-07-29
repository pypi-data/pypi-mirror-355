from pyfeed.feed import Feed, FeedItem
from pyfeed.merge import merge_feeds
from datetime import datetime

def test_merge_sorted():
    f1 = Feed("A", "", "", [FeedItem("1", "", "", datetime(2024, 1, 1))])
    f2 = Feed("B", "", "", [FeedItem("2", "", "", datetime(2025, 1, 1))])
    merged = merge_feeds([f1, f2])
    assert len(merged.items) == 2
    assert merged.items[0].title == "2"
