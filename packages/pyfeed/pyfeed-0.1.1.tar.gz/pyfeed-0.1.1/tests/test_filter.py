from pyfeed.feed import FeedItem
from pyfeed.filtering import filter_items

def test_keyword_filter():
    items = [
        FeedItem("Apple", "", "fruit", None),
        FeedItem("Banana", "", "yellow", None),
    ]
    result = filter_items(items, keyword="apple")
    assert len(result) == 1
    assert result[0].title == "Apple"
