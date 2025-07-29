from .feed import Feed
from itertools import chain


def merge_feeds(feeds):
    if not feeds:
        return Feed("Merged Feed", "", "", [])

    items = list(chain.from_iterable(feed.items for feed in feeds))
    items.sort(key=lambda x: x.pub_date or "", reverse=True)

    return Feed("Merged Feed", "", "", items)
