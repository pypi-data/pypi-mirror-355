from datetime import datetime
import re


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text) if text else ""


class FeedItem:
    def __init__(
        self,
        title,
        link,
        description,
        pub_date=None,
        guid=None,
        author=None,
        category=None,
        enclosure=None,
        source_url=None,
    ):
        self.title = title
        self.link = link
        self.description = description
        self.pub_date = pub_date
        self.guid = guid
        self.author = author
        self.category = category
        self.enclosure = enclosure
        self.source_url = source_url

    def to_dict(self):
        return {
            "title": self.title,
            "link": self.link,
            "description": strip_html(self.description),
            "pub_date": (
                self.pub_date.isoformat()
                if isinstance(self.pub_date, datetime)
                else self.pub_date
            ),
            "guid": self.guid or None,
            "author": self.author or None,
            "category": self.category or None,
            "enclosure": self.enclosure or None,
            "source_url": self.source_url or None,
        }


class Feed:
    def __init__(self, title, link, description, items):
        self.title = title
        self.link = link
        self.description = description
        self.items = items

    def to_dict(self):
        return {
            "title": self.title or None,
            "link": self.link or None,
            "description": self.description or None,
            "items": [item.to_dict() for item in self.items],
        }
