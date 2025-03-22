from textwrap import dedent

from sqlalchemy import (
    event,
    select,
)
from sqlalchemy.orm import Session

from libdib.repl import (
    NumberedCmd,
    InteractiveItemSelector,
    prompt_yes_no,
)

from worblehat.services import (
    create_bookcase_item_from_isbn,
    is_valid_isbn,
)

from worblehat.models import *

from .subclis import (
    AdvancedOptionsCli,
    BookcaseItemCli,
    select_bookcase_shelf,
    SearchCli,
)

# TODO: Category seems to have been forgotten. Maybe relevant interactivity should be added?
#       However, is there anyone who are going to search by category rather than just look in
#       the shelves?


class WorblehatCli(NumberedCmd):
    def __init__(self, sql_session: Session):
        super().__init__()
        self.sql_session = sql_session
        self.sql_session_dirty = False

        @event.listens_for(self.sql_session, "after_flush")
        def mark_session_as_dirty(*_):
            self.sql_session_dirty = True
            self.prompt_header = "(unsaved changes)"

        @event.listens_for(self.sql_session, "after_commit")
        @event.listens_for(self.sql_session, "after_rollback")
        def mark_session_as_clean(*_):
            self.sql_session_dirty = False
            self.prompt_header = None

    @classmethod
    def run_with_safe_exit_wrapper(cls, sql_session: Session):
        tool = cls(sql_session)
        while True:
            try:
                tool.cmdloop()
            except KeyboardInterrupt:
                if not tool.sql_session_dirty:
                    exit(0)
                try:
                    print()
                    if prompt_yes_no(
                        "Are you sure you want to exit without saving?", default=False
                    ):
                        raise KeyboardInterrupt
                except KeyboardInterrupt:
                    if tool.sql_session is not None:
                        tool.sql_session.rollback()
                    exit(0)

    def do_show_bookcase(self, arg: str):
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result

        for shelf in bookcase.shelfs:
            print(shelf.short_str())
            for item in shelf.items:
                print(f"  {item.name} - {item.amount} copies")

    def do_show_borrowed_queued(self, _: str):
        borrowed_items = self.sql_session.scalars(
            select(BookcaseItemBorrowing)
            .where(BookcaseItemBorrowing.delivered.is_(None))
            .order_by(BookcaseItemBorrowing.end_time),
        ).all()

        if len(borrowed_items) == 0:
            print("No borrowed items found.")
        else:
            print("Borrowed items:")
            for item in borrowed_items:
                print(
                    f"- {item.username} - {item.item.name} - to be delivered by {item.end_time.strftime('%Y-%m-%d')}"
                )

        print()

        queued_items = self.sql_session.scalars(
            select(BookcaseItemBorrowingQueue).order_by(
                BookcaseItemBorrowingQueue.entered_queue_time
            ),
        ).all()

        if len(queued_items) == 0:
            print("No queued items found.")
        else:
            print("Users in queue:")
            for item in queued_items:
                print(
                    f"- {item.username} - {item.item.name} - entered queue at {item.entered_queue_time.strftime('%Y-%m-%d')}"
                )

    def _create_bookcase_item(self, isbn: str):
        bookcase_item = create_bookcase_item_from_isbn(isbn, self.sql_session)
        if bookcase_item is None:
            print(f"Could not find data about item with ISBN {isbn} online.")
            print(
                "If you think this is not due to a bug, please add the book to openlibrary.org before continuing."
            )
            return
        else:
            print(
                dedent(f"""
            Found item:
              title: {bookcase_item.name}
              authors: {", ".join(a.name for a in bookcase_item.authors)}
              language: {bookcase_item.language}
            """)
            )

        print("Please select the bookcase where the item is placed:")
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result

        bookcase_item.shelf = select_bookcase_shelf(bookcase, self.sql_session)

        print("Please select the items media type:")
        media_type_selector = InteractiveItemSelector(
            cls=MediaType,
            sql_session=self.sql_session,
            default=self.sql_session.scalars(
                select(MediaType).where(MediaType.name.ilike("book")),
            ).one(),
        )

        media_type_selector.cmdloop()
        bookcase_item.media_type = media_type_selector.result

        username = input("Who owns this book? [PVV]> ")
        if username != "":
            bookcase_item.owner = username

        self.sql_session.add(bookcase_item)
        self.sql_session.flush()

    def default(self, isbn: str):
        isbn = isbn.strip()
        if not is_valid_isbn(isbn):
            super()._default(isbn)
            return

        if (
            existing_item := self.sql_session.scalars(
                select(BookcaseItem)
                .where(BookcaseItem.isbn == isbn)
                .join(BookcaseItemBorrowing)
                .join(BookcaseItemBorrowingQueue)
            ).one_or_none()
        ) is not None:
            print(f'\nFound existing item for isbn "{isbn}"')
            BookcaseItemCli(
                sql_session=self.sql_session,
                bookcase_item=existing_item,
            ).cmdloop()
            return

        if prompt_yes_no(
            f"Could not find item with ISBN '{isbn}'.\nWould you like to create it?",
            default=True,
        ):
            self._create_bookcase_item(isbn)

    def do_search(self, _: str):
        search_cli = SearchCli(self.sql_session)
        search_cli.cmdloop()
        if search_cli.result is not None:
            BookcaseItemCli(
                sql_session=self.sql_session,
                bookcase_item=search_cli.result,
            ).cmdloop()

    def do_show_slabbedasker(self, _: str):
        slubberter = self.sql_session.scalars(
            select(BookcaseItemBorrowing)
            .join(BookcaseItem)
            .where(
                BookcaseItemBorrowing.end_time < datetime.now(),
                BookcaseItemBorrowing.delivered.is_(None),
            )
            .order_by(
                BookcaseItemBorrowing.end_time,
            ),
        ).all()

        if len(slubberter) == 0:
            print("No slubberts found. Life is good.")
            return

        for slubbert in slubberter:
            print("Slubberter:")
            print(
                f"- {slubbert.username} - {slubbert.item.name} - {slubbert.end_time.strftime('%Y-%m-%d')}"
            )

    def do_advanced(self, _: str):
        AdvancedOptionsCli(self.sql_session).cmdloop()

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
            "doc": "Choose / Add item with its ISBN",
        },
        1: {
            "f": do_search,
            "doc": "Search",
        },
        2: {
            "f": do_show_bookcase,
            "doc": "Show a bookcase, and its items",
        },
        3: {
            "f": do_show_borrowed_queued,
            "doc": "Show borrowed/queued items",
        },
        4: {
            "f": do_show_slabbedasker,
            "doc": "Show slabbedasker",
        },
        5: {
            "f": do_save,
            "doc": "Save changes",
        },
        6: {
            "f": do_abort,
            "doc": "Abort changes",
        },
        7: {
            "f": do_advanced,
            "doc": "Advanced options",
        },
        9: {
            "f": do_exit,
            "doc": "Exit",
        },
    }
