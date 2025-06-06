from sqlalchemy import select
from sqlalchemy.orm import Session

from libdib.repl import (
    InteractiveItemSelector,
    NumberedCmd,
)
from worblehat.models import Bookcase, BookcaseShelf


class AdvancedOptionsCli(NumberedCmd):
    def __init__(self, sql_session: Session):
        super().__init__()
        self.sql_session = sql_session

    def do_add_bookcase(self, _: str):
        while True:
            name = input("Name of bookcase> ")
            if name == "":
                print("Error: name cannot be empty")
                continue

            if (
                self.sql_session.scalars(
                    select(Bookcase).where(Bookcase.name == name)
                ).one_or_none()
                is not None
            ):
                print(f"Error: a bookcase with name {name} already exists")
                continue

            break

        description = input("Description of bookcase> ")
        if description == "":
            description = None

        bookcase = Bookcase(name, description)
        self.sql_session.add(bookcase)
        self.sql_session.flush()

    def do_add_bookcase_shelf(self, arg: str):
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result

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
            self.sql_session.scalars(
                select(BookcaseShelf).where(
                    BookcaseShelf.bookcase == bookcase,
                    BookcaseShelf.column == column,
                    BookcaseShelf.row == row,
                )
            ).one_or_none()
            is not None
        ):
            print(
                f"Error: a bookshelf in bookcase {bookcase.name} with position c{column}-r{row} already exists"
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

    def do_list_bookcases(self, _: str):
        bookcase_shelfs = self.sql_session.scalars(
            select(BookcaseShelf)
            .join(Bookcase)
            .order_by(
                Bookcase.name,
                BookcaseShelf.column,
                BookcaseShelf.row,
            )
        ).all()

        bookcase_uid = None
        for shelf in bookcase_shelfs:
            if shelf.bookcase.uid != bookcase_uid:
                print(shelf.bookcase.short_str())
                bookcase_uid = shelf.bookcase.uid

            print(f"  {shelf.short_str()} - {sum(i.amount for i in shelf.items)} items")

    def do_done(self, _: str):
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
