from libdib.repl import (
    NumberedCmd,
    NumberedItemSelector,
)
from sqlalchemy.orm import Session

from worblehat.queries import (
    list_bookcase_items_by_owner,
    search_authors_by_name,
    search_bookcase_item_owners,
    search_bookcase_items_by_title,
)


class SearchCli(NumberedCmd):
    def __init__(self, sql_session: Session) -> None:
        super().__init__()
        self.sql_session = sql_session
        self.result = None

    def do_search_all(self, _: str) -> None:
        print("TODO: Implement search all")

    def do_search_title(self, _: str) -> bool | None:
        while (input_text := input("Enter title: ")) == "":
            pass

        items = search_bookcase_items_by_title(self.sql_session, input_text)

        if len(items) == 0:
            print("No items found.")
            return None

        selector = NumberedItemSelector(
            items=items,
            stringify=lambda item: f"{item.name} ({item.isbn})",
        )
        selector.cmdloop()
        if selector.result is not None:
            self.result = selector.result
            return True
        return None

    def do_search_author(self, _: str) -> bool | None:
        while (input_text := input("Enter author name: ")) == "":
            pass

        author = search_authors_by_name(self.sql_session, input_text)

        if len(author) == 0:
            print("No authors found.")
            return None
        if len(author) == 1:
            selected_author = author[0]
            print("Found author:")
            print(
                f"  {selected_author.name} ({sum(item.amount for item in selected_author.items)} items)",
            )
        else:
            selector = NumberedItemSelector(
                items=author,
                stringify=lambda author: f"{author.name} ({sum(item.amount for item in author.items)} items)",
            )
            selector.cmdloop()
            if selector.result is None:
                return None
            selected_author = selector.result

        selector = NumberedItemSelector(
            items=list(selected_author.items),
            stringify=lambda item: f"{item.name} ({item.isbn})",
        )
        selector.cmdloop()
        if selector.result is not None:
            self.result = selector.result
            return True
        return None

    def do_search_owner(self, _: str) -> bool | None:
        while (input_text := input("Enter username: ")) == "":
            pass

        users = search_bookcase_item_owners(self.sql_session, input_text)

        if len(users) == 0:
            print("No users found.")
            return None
        if len(users) == 1:
            selected_user = users[0]
            print("Found user:")
            print(f"  {selected_user}")
        else:
            selector = NumberedItemSelector(items=users)
            selector.cmdloop()
            if selector.result is None:
                return None
            selected_user = selector.result

        items = list_bookcase_items_by_owner(self.sql_session, selected_user)

        selector = NumberedItemSelector(
            items=items,
            stringify=lambda item: f"{item.name} ({item.isbn})",
        )
        selector.cmdloop()
        if selector.result is not None:
            self.result = selector.result
            return True
        return None

    def do_done(self, _: str) -> bool:
        return True

    funcs = {
        1: {
            "f": do_search_all,
            "doc": "Search everything",
        },
        2: {
            "f": do_search_title,
            "doc": "Search by title",
        },
        3: {
            "f": do_search_author,
            "doc": "Search by author",
        },
        4: {
            "f": do_search_owner,
            "doc": "Search by owner",
        },
        9: {
            "f": do_done,
            "doc": "Done",
        },
    }
