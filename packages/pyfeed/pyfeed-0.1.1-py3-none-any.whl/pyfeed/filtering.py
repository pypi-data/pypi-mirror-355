def filter_items(items, keyword=None, category=None, author=None):
    def match(item):
        return (
            (
                not keyword
                or keyword.lower() in item.title.lower()
                or keyword.lower() in item.description.lower()
            )
            and (not category or category.lower() == (item.category or "").lower())
            and (not author or author.lower() in (item.author or "").lower())
        )

    return [item for item in items if match(item)]
