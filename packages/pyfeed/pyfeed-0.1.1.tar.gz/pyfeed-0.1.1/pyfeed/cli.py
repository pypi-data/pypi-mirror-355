import argparse
import json
from .parser import parse
from .merge import merge_feeds
from .feed import Feed


def main():
    parser = argparse.ArgumentParser(description="pyfeed: simple RSS/Atom parser")
    parser.add_argument("urls", nargs="+", help="Feed URLs to parse")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--filter", metavar="KEYWORD", help="Filter items by keyword")
    parser.add_argument("--limit", type=int, help="Limit number of items")
    parser.add_argument("--output", help="Save output to file")
    args = parser.parse_args()

    feeds = [parse(url) for url in args.urls]
    merged = merge_feeds(feeds)

    items = merged.items
    if args.filter:
        from .filtering import filter_items

        items = filter_items(items, keyword=args.filter)

    if args.limit:
        items = items[: args.limit]

    merged.items = items

    output = json.dumps(merged.to_dict(), indent=2 if args.json else None)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
    else:
        print(output)


if __name__ == "__main__":
    main()
