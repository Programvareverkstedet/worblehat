from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import Bookcase, BookcaseShelf


def find_bookcase_shelf(
    sql_session: Session,
    bookcase: Bookcase,
    column: int,
    row: int,
) -> BookcaseShelf | None:
    return sql_session.scalars(
        select(BookcaseShelf).where(
            BookcaseShelf.bookcase == bookcase,
            BookcaseShelf.column == column,
            BookcaseShelf.row == row,
        ),
    ).one_or_none()


def list_bookcase_shelfs_ordered(sql_session: Session) -> list[BookcaseShelf]:
    return list(
        sql_session.scalars(
            select(BookcaseShelf)
            .join(Bookcase)
            .order_by(
                Bookcase.name,
                BookcaseShelf.column,
                BookcaseShelf.row,
            ),
        ).all(),
    )


def list_bookcase_shelf_positions(
    sql_session: Session,
    bookcase: Bookcase,
    column: int | None = None,
    row: int | None = None,
) -> list[tuple[int, int]]:
    query = select(BookcaseShelf.row, BookcaseShelf.column).where(
        BookcaseShelf.bookcase == bookcase,
    )
    if column is not None:
        query = query.where(BookcaseShelf.column == column)
    if row is not None:
        query = query.where(BookcaseShelf.row == row)
    return [tuple(r) for r in sql_session.execute(query)]
