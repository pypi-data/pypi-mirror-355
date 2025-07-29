import xml.etree.ElementTree as ET
from urllib.request import urlopen
from dateutil import parser as date_parser
from .feed import Feed, FeedItem


def parse(url):
    try:
        with urlopen(url) as response:
            xml_data = response.read()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch URL: {e}")
    return parse_feed(xml_data)


def parse_feed(xml_data):
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML feed: {e}")

    if root.tag == "rss":
        return parse_rss(root)
    elif "feed" in root.tag:
        return parse_atom(root)
    else:
        raise ValueError("Unsupported feed format")


def parse_rss(root):
    channel = root.find("channel")
    if channel is None:
        raise ValueError("No <channel> found in RSS feed")

    title = get_text(channel.find("title"))
    link = get_text(channel.find("link"))
    description = get_text(channel.find("description"))

    items = []
    for item_elem in channel.findall("item"):
        items.append(
            FeedItem(
                title=get_text(item_elem.find("title")),
                link=get_text(item_elem.find("link")),
                description=get_text(item_elem.find("description")),
                pub_date=parse_date(get_text(item_elem.find("pubDate"))),
                guid=get_text(item_elem.find("guid")),
                author=get_text(item_elem.find("author")),
                category=get_text(item_elem.find("category")),
                enclosure=(
                    item_elem.find("enclosure").attrib.get("url")
                    if item_elem.find("enclosure") is not None
                    else None
                ),
            )
        )

    return Feed(title, link, description, items)


def parse_atom(root):
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    title = get_text(root.find("atom:title", ns))
    link_elem = root.find("atom:link[@rel='alternate']", ns) or root.find(
        "atom:link", ns
    )
    link = link_elem.attrib.get("href") if link_elem is not None else ""
    subtitle = get_text(root.find("atom:subtitle", ns))

    items = []
    for entry in root.findall("atom:entry", ns):
        items.append(
            FeedItem(
                title=get_text(entry.find("atom:title", ns)),
                link=(
                    entry.find("atom:link", ns).attrib.get("href")
                    if entry.find("atom:link", ns) is not None
                    else ""
                ),
                description=get_text(entry.find("atom:summary", ns))
                or get_text(entry.find("atom:content", ns)),
                pub_date=parse_date(
                    get_text(entry.find("atom:updated", ns))
                    or get_text(entry.find("atom:published", ns))
                ),
                guid=get_text(entry.find("atom:id", ns)),
                author=get_text(entry.find("atom:author/atom:name", ns)),
                category=(
                    entry.find("atom:category", ns).attrib.get("term")
                    if entry.find("atom:category", ns) is not None
                    else None
                ),
                enclosure=(
                    entry.find("atom:link[@rel='enclosure']", ns).attrib.get("href")
                    if entry.find("atom:link[@rel='enclosure']", ns) is not None
                    else None
                ),
            )
        )

    return Feed(title, link, subtitle, items)


def get_text(element):
    return element.text.strip() if element is not None and element.text else ""


def parse_date(value):
    try:
        return date_parser.parse(value)
    except Exception:
        return None
