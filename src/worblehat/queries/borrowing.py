from datetime import datetime, timedelta

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from worblehat.models import BookcaseItem, Borrowing, BorrowingEventType, BorrowingLog

DEFAULT_LOAN_DAYS = 30


def list_active_borrowings(sql_session: Session) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing).order_by(Borrowing.due_time),
        ).all(),
    )


def list_active_borrowings_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing)
            .where(Borrowing.fk_bookcase_item_uid == item.uid)
            .order_by(Borrowing.due_time),
        ).all(),
    )


def get_active_borrowing(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
) -> Borrowing | None:
    return sql_session.scalars(
        select(Borrowing).where(
            Borrowing.username == username,
            Borrowing.fk_bookcase_item_uid == item.uid,
        ),
    ).one_or_none()


def has_active_borrowing(sql_session: Session, username: str, item: BookcaseItem) -> bool:
    return sql_session.scalar(
        select(
            exists().where(
                Borrowing.username == username,
                Borrowing.fk_bookcase_item_uid == item.uid,
            ),
        ),
    )


def list_borrowings_for_isbn(sql_session: Session, isbn: str) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing)
            .join(
                BookcaseItem,
                BookcaseItem.uid == Borrowing.fk_bookcase_item_uid,
            )
            .where(BookcaseItem.isbn == isbn)
            .order_by(Borrowing.username),
        ).all(),
    )


def list_overdue_borrowings(sql_session: Session) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing)
            .where(Borrowing.due_time < datetime.now())
            .order_by(Borrowing.due_time),
        ).all(),
    )


def list_borrowing_log_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[BorrowingLog]:
    return list(
        sql_session.scalars(
            select(BorrowingLog)
            .where(BorrowingLog.fk_bookcase_item_uid == item.uid)
            .order_by(BorrowingLog.due_time),
        ).all(),
    )


def borrow_item(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    loan_days: int = DEFAULT_LOAN_DAYS,
    _unsafe: bool = False,
) -> tuple[Borrowing, BorrowingLog]:
    if not _unsafe:
        if has_active_borrowing(sql_session, username, item):
            raise ValueError(f"{username} already has an active borrowing of this item")
        if len(list_active_borrowings_for_item(sql_session, item)) >= item.amount:
            raise ValueError("No available copies of this item to borrow")

    due_time = datetime.now() + timedelta(days=loan_days)
    log_entry = BorrowingLog(username, item, BorrowingEventType.BORROWED, due_time=due_time)
    sql_session.add(log_entry)
    sql_session.flush()
    current = sql_session.get_one(Borrowing, (item.uid, username))
    return current, log_entry


def renew_borrowing(
    sql_session: Session,
    borrowing: Borrowing,
    loan_days: int = DEFAULT_LOAN_DAYS,
    _unsafe: bool = False,
) -> Borrowing:
    if (
        not _unsafe
        and get_active_borrowing(sql_session, borrowing.username, borrowing.item) is None
    ):
        raise ValueError(f"{borrowing.username} does not currently have this item borrowed")

    due_time = datetime.now() + timedelta(days=loan_days)
    sql_session.add(
        BorrowingLog(
            borrowing.username,
            borrowing.item,
            BorrowingEventType.RENEWED,
            due_time=due_time,
        ),
    )
    sql_session.flush()
    sql_session.refresh(borrowing)
    return borrowing


def return_item(sql_session: Session, borrowing: Borrowing, _unsafe: bool = False) -> None:
    if (
        not _unsafe
        and get_active_borrowing(sql_session, borrowing.username, borrowing.item) is None
    ):
        raise ValueError(f"{borrowing.username} does not currently have this item borrowed")

    sql_session.add(
        BorrowingLog(borrowing.username, borrowing.item, BorrowingEventType.RETURNED),
    )
    sql_session.flush()
    sql_session.expunge(borrowing)
