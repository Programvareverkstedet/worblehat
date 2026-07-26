from libdib.repl import InteractiveItemSelector
from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseShelf,
)
from worblehat.queries import (
    find_bookcase_shelf,
    list_bookcase_shelf_positions,
)


def select_bookcase_shelf(
    bookcase: Bookcase,
    sql_session: Session,
    prompt: str = "Please select the shelf where the item is placed (col-row):",
) -> BookcaseShelf:
    def __complete_bookshelf_selection(session: Session, cls: type, arg: str):
        args = arg.split("-")
        column = None
        row = None
        try:
            if arg != "" and len(args) > 0:
                column = int(args[0])
            if len(args) > 1:
                row = int(args[1])
        except ValueError:
            return []

        result = list_bookcase_shelf_positions(session, bookcase, column, row)
        return [f"{c}-{r}" for r, c in result]

    def __execute_bookshelf_selection(session: Session, cls: type, arg: str):
        shelf = find_bookcase_shelf(
            session,
            bookcase,
            int(arg.split("-")[0]),
            int(arg.split("-")[1]),
        )
        return [shelf] if shelf is not None else []

    print(prompt)
    bookcase_shelf_selector = InteractiveItemSelector(
        cls=BookcaseShelf,
        sql_session=sql_session,
        execute_selection=__execute_bookshelf_selection,
        complete_selection=__complete_bookshelf_selection,
    )

    bookcase_shelf_selector.cmdloop()
    result = bookcase_shelf_selector.result
    assert isinstance(result, BookcaseShelf)
    return result
