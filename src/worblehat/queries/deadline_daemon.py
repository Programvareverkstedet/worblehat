from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from worblehat.models import (
    BookcaseItemBorrowing,
    BookcaseItemBorrowingQueue,
    DeadlineDaemonLastRunDatetime,
)


def _sql_subtract_date(sql_session: Session, x: datetime, y: timedelta):
    if sql_session.bind.dialect.name == "sqlite":
        # SQLite does not support timedelta in queries
        return func.datetime(x, f"-{y.days} days")
    if sql_session.bind.dialect.name == "postgresql":
        return x - y
    raise NotImplementedError(
        f"Unsupported dialect: {sql_session.bind.dialect.name}",
    )


def find_last_run(sql_session: Session) -> DeadlineDaemonLastRunDatetime | None:
    return sql_session.scalars(
        select(DeadlineDaemonLastRunDatetime),
    ).one_or_none()


def list_close_deadline_borrowings(
    sql_session: Session,
    day: int,
    last_run_datetime: datetime,
    current_run_datetime: datetime,
) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing).where(
                _sql_subtract_date(
                    sql_session,
                    BookcaseItemBorrowing.end_time,
                    timedelta(days=day),
                ).between(
                    last_run_datetime,
                    current_run_datetime,
                ),
                BookcaseItemBorrowing.delivered.is_(None),
            ),
        ).all(),
    )


def list_undelivered_overdue_borrowings(
    sql_session: Session,
    current_run_datetime: datetime,
) -> list[BookcaseItemBorrowing]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowing).where(
                BookcaseItemBorrowing.end_time < current_run_datetime,
                BookcaseItemBorrowing.delivered.is_(None),
            ),
        ).all(),
    )


def list_newly_available_queue_items(
    sql_session: Session,
    last_run_datetime: datetime,
    current_run_datetime: datetime,
) -> list[BookcaseItemBorrowingQueue]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue)
            .join(
                BookcaseItemBorrowing,
                BookcaseItemBorrowing.fk_bookcase_item_uid
                == BookcaseItemBorrowingQueue.fk_bookcase_item_uid,
            )
            .where(
                BookcaseItemBorrowingQueue.expired.is_(False),
                BookcaseItemBorrowing.delivered.is_not(None),
                BookcaseItemBorrowing.delivered.between(
                    last_run_datetime,
                    current_run_datetime,
                ),
            )
            .order_by(BookcaseItemBorrowingQueue.entered_queue_time)
            .group_by(BookcaseItemBorrowingQueue.fk_bookcase_item_uid),
        ).all(),
    )


def list_expiring_queue_positions(
    sql_session: Session,
    last_run_datetime: datetime,
    current_run_datetime: datetime,
) -> list[BookcaseItemBorrowingQueue]:
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue)
            .join(
                BookcaseItemBorrowing,
                BookcaseItemBorrowing.fk_bookcase_item_uid
                == BookcaseItemBorrowingQueue.fk_bookcase_item_uid,
            )
            .where(
                BookcaseItemBorrowingQueue.item_became_available_time.between(
                    last_run_datetime,
                    current_run_datetime,
                ),
            ),
        ).all(),
    )


def list_overdue_queue_positions(
    sql_session: Session,
    queue_position_expiry_days: int,
    current_run_datetime: datetime,
) -> list[BookcaseItemBorrowingQueue]:
    expiry_cutoff = current_run_datetime - timedelta(days=queue_position_expiry_days)
    return list(
        sql_session.scalars(
            select(BookcaseItemBorrowingQueue).where(
                BookcaseItemBorrowingQueue.item_became_available_time < expiry_cutoff,
                BookcaseItemBorrowingQueue.expired.is_(False),
            ),
        ).all(),
    )


def find_next_queue_position(
    sql_session: Session,
    item_uid: int,
) -> BookcaseItemBorrowingQueue | None:
    return sql_session.scalars(
        select(BookcaseItemBorrowingQueue)
        .where(
            BookcaseItemBorrowingQueue.fk_bookcase_item_uid == item_uid,
            BookcaseItemBorrowingQueue.item_became_available_time.is_(None),
        )
        .order_by(BookcaseItemBorrowingQueue.entered_queue_time)
        .limit(1),
    ).one_or_none()
