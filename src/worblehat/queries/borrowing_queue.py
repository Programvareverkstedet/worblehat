from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import BookcaseItem, BookcaseItemBorrowingQueue


def list_all_queue_items(sql_session: Session) -> list[BookcaseItemBorrowingQueue]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue).order_by(
                BookcaseItemBorrowingQueue.entered_queue_time,
            ),
        ).all(),
    )


def is_in_borrowing_queue(sql_session: Session, username: str, item: BookcaseItem) -> bool:
    return (
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue).where(
                BookcaseItemBorrowingQueue.username == username,
                BookcaseItemBorrowingQueue.item == item,
            ),
        ).one_or_none()
        is not None
    )


def list_pending_queue_items_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[BookcaseItemBorrowingQueue]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue)
            .where(
                BookcaseItemBorrowingQueue.item == item,
                BookcaseItemBorrowingQueue.item_became_available_time.is_(None),
            )
            .order_by(BookcaseItemBorrowingQueue.entered_queue_time),
        ).all(),
    )
