from libdib.repl import (
    InteractiveItemSelector,
    NumberedCmd,
)
from sqlalchemy.orm import Session

from worblehat.models import Bookcase, BookcaseShelf
from worblehat.queries import (
    find_bookcase_by_name,
    find_bookcase_shelf,
    list_bookcase_shelfs_ordered,
)


class AdvancedOptionsCli(NumberedCmd):
    def __init__(self, sql_session: Session) -> None:
        super().__init__()
        self.sql_session = sql_session

    def do_add_bookcase(self, _: str) -> None:
        while True:
            name = input("Name of bookcase> ")
            if name == "":
                print("Error: name cannot be empty")
                continue

            if find_bookcase_by_name(self.sql_session, name) is not None:
                print(f"Error: a bookcase with name {name} already exists")
                continue

            break

        description = input("Description of bookcase> ")
        if description == "":
            description = None

        bookcase = Bookcase(name, description)
        self.sql_session.add(bookcase)
        self.sql_session.flush()

    def do_add_bookcase_shelf(self, arg: str) -> None:
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result
        assert isinstance(bookcase, Bookcase)

        while True:
            column = input("Column> ")
            try:
                column = int(column)
            except ValueError:
                print("Error: column must be a number")
                continue
            break

        while True:
            row = input("Row> ")
            try:
                row = int(row)
            except ValueError:
                print("Error: row must be a number")
                continue
            break

        if (
            find_bookcase_shelf(self.sql_session, bookcase, column, row)
            is not None
        ):
            print(
                f"Error: a bookshelf in bookcase {bookcase.name} with position c{column}-r{row} already exists",
            )
            return

        description = input("Description> ")
        if description == "":
            description = None

        shelf = BookcaseShelf(
            row,
            column,
            bookcase,
            description,
        )
        self.sql_session.add(shelf)
        self.sql_session.flush()

    def do_list_bookcases(self, _: str) -> None:
        bookcase_shelfs = list_bookcase_shelfs_ordered(self.sql_session)

        bookcase_uid = None
        for shelf in bookcase_shelfs:
            if shelf.bookcase.uid != bookcase_uid:
                print(shelf.bookcase.short_str())
                bookcase_uid = shelf.bookcase.uid

            print(f"  {shelf.short_str()} - {sum(i.amount for i in shelf.items)} items")

    def do_done(self, _: str) -> bool:
        return True

    funcs = {
        1: {
            "f": do_add_bookcase,
            "doc": "Add bookcase",
        },
        2: {
            "f": do_add_bookcase_shelf,
            "doc": "Add bookcase shelf",
        },
        3: {
            "f": do_list_bookcases,
            "doc": "List all bookcases",
        },
        9: {
            "f": do_done,
            "doc": "Done",
        },
    }
