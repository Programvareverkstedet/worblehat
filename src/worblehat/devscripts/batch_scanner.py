from worblehat.cli.subclis import select_bookcase_shelf
from sqlalchemy import select, event
from sqlalchemy.orm.session import Session
from worblehat.models import Bookcase, BookcaseShelf
from worblehat.services.metadata_fetchers import fetch_metadata_from_multiple_sources
from worblehat.services import is_valid_isbn
from pprint import pprint
from libdib.repl import (
  NumberedCmd,
  prompt_yes_no,
)

class BatchScanner(NumberedCmd):
    def __init__(self, sql_session: Session):
        super().__init__()
        self.sql_session = sql_session
        self.sql_session_dirty = False
        self.bookcase_shelf = None
        self.prompt_header = "[SHELF| NONE]"

        @event.listens_for(self.sql_session, "after_flush")
        def mark_session_as_dirty(*_):
            self.sql_session_dirty = True
            self.prompt_header = "(unsaved changes)"

        @event.listens_for(self.sql_session, "after_commit")
        @event.listens_for(self.sql_session, "after_rollback")
        def mark_session_as_clean(*_):
            self.sql_session_dirty = False
            self.prompt_header = None


    def _set_bookcase_shelf(self, bookcase_shelf: BookcaseShelf):
        self.bookcase_shelf = bookcase_shelf
        self.prompt_header = f"[SHELF| {bookcase_shelf.bookcase.uid} {bookcase_shelf.bookcase.description} / {bookcase_shelf.column}-{bookcase_shelf.row}: {bookcase_shelf.description}]"


    def default(self, isbn: str):
        isbn = isbn.strip()
        if not is_valid_isbn(isbn):
            super()._default(isbn)
            return

        if self.bookcase_shelf is None:
            print("Please set the bookcase shelf first.")
            return

        print(f"Scanned ISBN: {isbn}")

        data = fetch_metadata_from_multiple_sources(isbn)

        pprint(data)


    def do_set_bookcase_shelf(self, _: str):
        bookcase = self._choose_bookcase(self.sql_session)

        print()

        self._print_bookcase_shelves(
            sql_session=self.sql_session,
            bookcase=bookcase,
        )

        print()

        bookcase_shelf = select_bookcase_shelf(
            sql_session=self.sql_session,
            bookcase=bookcase,
        )

        self._set_bookcase_shelf(bookcase_shelf)

        print(f"Bookcase shelf set to {bookcase_shelf}")

    def _choose_bookcase(
        self,
        sql_session: Session,
    ) -> Bookcase:
        bookcases = sql_session.scalars(
            select(Bookcase)
        ).all()

        while True:
            print("Available bookcases:")
            for bookcase in bookcases:
                print(f"  {bookcase.name} - {bookcase.description}")

            bookcase_name = input("Choose a bookcase> ").strip()

            bookcase = sql_session.scalars(
                select(Bookcase).where(Bookcase.name == bookcase_name)
            ).one_or_none()

            if not bookcase:
                print(f"Bookcase {bookcase_name} not found")
                continue

            return bookcase

    def _print_bookcase_shelves(
        self,
        sql_session: Session,
        bookcase: Bookcase,
    ) -> None:
        shelves = sql_session.scalars(
            select(BookcaseShelf).where(BookcaseShelf.bookcase == bookcase)
        ).all()
        min_col = min([shelf.column for shelf in shelves])
        max_col = max([shelf.column for shelf in shelves])
        min_row = min([shelf.row for shelf in shelves])
        max_row = max([shelf.row for shelf in shelves])

        print('Available shelves:')
        for col in range(min_col, max_col + 1):
            for row in range(min_row, max_row + 1):
                shelf = sql_session.scalars(
                    select(BookcaseShelf).where(
                        BookcaseShelf.bookcase == bookcase,
                        BookcaseShelf.column == col,
                        BookcaseShelf.row == row,
                    )
                ).one_or_none()
                if shelf:
                    print(f"{col}-{row}: {shelf.description}")
                else:
                    print(f"{col}-{row}: None")

    def do_save(self, _: str):
        if not self.sql_session_dirty:
            print("No changes to save.")
            return
        self.sql_session.commit()

    def do_abort(self, _: str):
        if not self.sql_session_dirty:
            print("No changes to abort.")
            return
        self.sql_session.rollback()

    def do_exit(self, _: str):
        if self.sql_session_dirty:
            if prompt_yes_no("Would you like to save your changes?"):
                self.sql_session.commit()
            else:
                self.sql_session.rollback()
        exit(0)

    funcs = {
        0: {
            "f": default,
            "doc": "Add item with its ISBN",
        },
        1: {
            'f' : do_set_bookcase_shelf,
            'doc' : 'Select shelf',
        },
        7: {
            "f": do_save,
            "doc": "Save changes",
        },
        8: {
            "f": do_abort,
            "doc": "Abort changes",
        },
        9: {
            "f": do_exit,
            "doc": "Exit",
        },
    }
