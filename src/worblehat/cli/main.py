import contextlib
import logging
import sys
import traceback
from pathlib import Path
from textwrap import dedent
from time import ctime, time

from libdib.repl import (
    InteractiveItemSelector,
    NumberedCmd,
    prompt_yes_no,
)
from sqlalchemy import event
from sqlalchemy.orm import Session

from worblehat.models import *
from worblehat.queries import (
    find_bookcase_item_by_isbn,
    list_active_borrowings,
    list_all_queue_items,
    list_overdue_borrowings,
)
from worblehat.services import (
    Config,
    create_bookcase_item_from_isbn,
    is_valid_isbn,
)

from .subclis import (
    AdvancedOptionsCli,
    BookcaseItemCli,
    SearchCli,
    select_bookcase_shelf,
)

# TODO: Category seems to have been forgotten. Maybe relevant interactivity should be added?
#       However, is there anyone who are going to search by category rather than just look in
#       the shelves?


class WorblehatCli(NumberedCmd):
    def __init__(self, sql_session: Session) -> None:
        super().__init__()
        self.sql_session = sql_session
        self.sql_session_dirty = False

        @event.listens_for(self.sql_session, "after_flush")
        def mark_session_as_dirty(*_) -> None:
            self.sql_session_dirty = True
            self.prompt_header = "(unsaved changes)"

        @event.listens_for(self.sql_session, "after_commit")
        @event.listens_for(self.sql_session, "after_rollback")
        def mark_session_as_clean(*_) -> None:
            self.sql_session_dirty = False
            self.prompt_header = None

    def run_with_safe_exit_wrapper(self) -> None:
        while True:
            try:
                self.cmdloop()
            except KeyboardInterrupt:
                print("\n\n-----------------\n")
                self.do_exit("Exit")
            except Exception:
                self._write_crashdump()
                print("Restarting main menu.\n")
                with contextlib.suppress(Exception):
                    self.sql_session.rollback()

    def _write_crashdump(self) -> None:
        try:
            from .._version import commit_id, version
        except ImportError:
            commit_id = None
            version = None

        print("Something went wrong.")
        print(f"{sys.exc_info()[0]}: {sys.exc_info()[1]}")

        crashdump_dir = Path(Config["general.crashdump_dir"])
        crashdump_dir.mkdir(parents=True, exist_ok=True)
        crashdump_path = crashdump_dir / f"crashdump_{int(time())}.log"

        with crashdump_path.open("w") as f:
            f.write(f"Worblehat crashdump @ {ctime()}\n")
            if version is not None:
                f.write(f"Worblehat version {version}, commit {commit_id or '<unknown>'}\n")
            f.write("\n")
            traceback.print_exc(file=f)

        logging.error(
            "Unhandled exception in CLI loop: %s: %s (see %s for full traceback)",
            sys.exc_info()[0].__name__,
            sys.exc_info()[1],
            crashdump_path,
        )

    def do_show_bookcase(self, arg: str) -> None:
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result
        if bookcase == None:
            return

        for shelf in bookcase.shelfs:
            print(shelf.short_str())
            for item in shelf.items:
                print(f"  {item.name} - {item.amount} copies")

    def do_show_borrowed_queued(self, _: str) -> None:
        borrowed_items = list_active_borrowings(self.sql_session)

        if len(borrowed_items) == 0:
            print("No borrowed items found.")
        else:
            print("Borrowed items:")
            for item in borrowed_items:
                print(
                    f"- {item.username} - {item.item.name} - to be delivered by {item.due_time.strftime('%Y-%m-%d')}",
                )

        print()

        queued_items = list_all_queue_items(self.sql_session)

        if len(queued_items) == 0:
            print("No queued items found.")
        else:
            print("Users in queue:")
            for item in queued_items:
                print(
                    f"- {item.username} - {item.item.name} - entered queue at {item.entered_queue_time.strftime('%Y-%m-%d')}",
                )

    def _create_bookcase_item(self, isbn: str) -> None:
        bookcase_item = create_bookcase_item_from_isbn(isbn)
        if bookcase_item is None:
            print(f"Could not find data about item with ISBN {isbn} online.")
            print(
                "If you think this is not due to a bug, please add the book to openlibrary.org before continuing.",
            )
            return
        print(
            dedent(f"""
            Found item:
              title: {bookcase_item.name}
              authors: {", ".join(a.name for a in bookcase_item.authors)}
              language: {bookcase_item.language}
            """),
        )

        print("Please select the bookcase where the item is placed:")
        bookcase_selector = InteractiveItemSelector(
            cls=Bookcase,
            sql_session=self.sql_session,
        )
        bookcase_selector.cmdloop()
        bookcase = bookcase_selector.result
        if bookcase == None:
            return

        bookcase_item.shelf = select_bookcase_shelf(bookcase, self.sql_session)

        print("Please select the items media type:")
        media_type_selector = InteractiveItemSelector(
            cls=MediaType,
            sql_session=self.sql_session,
            execute_selection=lambda _session, cls, arg: [m for m in cls if m.name == arg.upper()],
            complete_selection=lambda _session, cls, text: [
                m.name for m in cls if m.name.startswith(text.upper())
            ],
            default=MediaType.BOOK,
        )

        media_type_selector.cmdloop()
        bookcase_item.media_type = media_type_selector.result
        if bookcase_item.media_type == None:
            return

        username = input("Who owns this book? [PVV]> ")
        if username != "":
            bookcase_item.owner = username

        self.sql_session.add(bookcase_item)
        self.sql_session.flush()

    def default(self, isbn: str) -> None:
        isbn = isbn.strip()
        if not is_valid_isbn(isbn):
            super()._default(isbn)
            return

        if (
            existing_item := find_bookcase_item_by_isbn(
                self.sql_session,
                isbn,
            )
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

    def do_search(self, _: str) -> None:
        search_cli = SearchCli(self.sql_session)
        search_cli.cmdloop()
        if search_cli.result is not None:
            BookcaseItemCli(
                sql_session=self.sql_session,
                bookcase_item=search_cli.result,
            ).cmdloop()

    def do_show_slabbedasker(self, _: str) -> None:
        slubberter = list_overdue_borrowings(self.sql_session)

        if len(slubberter) == 0:
            print("No slubberts found. Life is good.")
            return

        for slubbert in slubberter:
            print("Slubberter:")
            print(
                f"- {slubbert.username} - {slubbert.item.name} - {slubbert.due_time.strftime('%Y-%m-%d')}",
            )

    def do_advanced(self, _: str) -> None:
        AdvancedOptionsCli(self.sql_session).cmdloop()

    def do_save(self, _: str) -> None:
        if not self.sql_session_dirty:
            print("No changes to save.")
            return
        self.sql_session.commit()

    def do_abort(self, _: str) -> None:
        if not self.sql_session_dirty:
            print("No changes to abort.")
            return
        self.sql_session.rollback()

    def do_exit(self, _: str) -> None:
        if self.sql_session_dirty:
            if prompt_yes_no("Would you like to save your changes?"):
                self.sql_session.commit()
            else:
                self.sql_session.rollback()
        if Config["general.quit_allowed"]:
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
