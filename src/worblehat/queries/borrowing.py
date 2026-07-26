from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import BookcaseItem, BookcaseItemBorrowing


def list_active_borrowings(sql_session: Session) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing)
            .where(BookcaseItemBorrowing.delivered.is_(None))
            .order_by(BookcaseItemBorrowing.end_time),
        ).all(),
    )


def list_active_borrowings_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing)
            .where(
                BookcaseItemBorrowing.item == item,
                BookcaseItemBorrowing.delivered.is_(None),
            )
            .order_by(BookcaseItemBorrowing.end_time),
        ).all(),
    )


def has_active_borrowing(sql_session: Session, username: str, item: BookcaseItem) -> bool:
    return (
        sql_session.scalars(
            select(BookcaseItemBorrowing).where(
                BookcaseItemBorrowing.username == username,
                BookcaseItemBorrowing.item == item,
                BookcaseItemBorrowing.delivered.is_(None),
            ),
        ).one_or_none()
        is not None
    )


def list_borrowings_for_isbn(sql_session: Session, isbn: str) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing)
            .join(
                BookcaseItem,
                BookcaseItem.uid == BookcaseItemBorrowing.fk_bookcase_item_uid,
            )
            .where(BookcaseItem.isbn == isbn)
            .order_by(BookcaseItemBorrowing.username),
        ).all(),
    )


def list_overdue_borrowings(sql_session: Session) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing)
            .join(BookcaseItem)
            .where(
                BookcaseItemBorrowing.end_time < datetime.now(),
                BookcaseItemBorrowing.delivered.is_(None),
            )
            .order_by(BookcaseItemBorrowing.end_time),
        ).all(),
    )
