import pytest
from pyfeed.parser import parse_feed
from pyfeed.feed import Feed, FeedItem
from datetime import datetime

RSS_SAMPLE = b"""<?xml version="1.0"?>
<rss version="2.0">
<channel>
  <title>RSS Title</title>
  <link>http://rss.com</link>
  <description>RSS Desc</description>
  <item>
    <title>One</title>
    <link>http://rss.com/1</link>
    <description>Post</description>
    <pubDate>Mon, 10 Jun 2024 10:00:00 GMT</pubDate>
    <guid>abc</guid>
  </item>
</channel>
</rss>"""

ATOM_SAMPLE = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Title</title>
  <link href="http://atom.com/"/>
  <subtitle>Atom Desc</subtitle>
  <entry>
    <title>Two</title>
    <link href="http://atom.com/2"/>
    <id>tag:atom.com,2024:2</id>
    <updated>2024-06-11T12:34:56Z</updated>
    <summary>Second post</summary>
  </entry>
</feed>"""

def test_parse_rss_sample():
    feed = parse_feed(RSS_SAMPLE)
    assert isinstance(feed, Feed)
    assert feed.title == "RSS Title"
    assert len(feed.items) == 1
    item = feed.items[0]
    assert item.title == "One"
    assert isinstance(item.pub_date, datetime)

def test_parse_atom_sample():
    feed = parse_feed(ATOM_SAMPLE)
    assert isinstance(feed, Feed)
    assert feed.description == "Atom Desc"
    assert len(feed.items) == 1
    item = feed.items[0]
    assert item.link == "http://atom.com/2"
    assert isinstance(item.pub_date, datetime)
