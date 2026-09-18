from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import SQLColumnExpression

from worblehat.models import (
    Borrowing,
    BorrowingEventType,
    BorrowingLog,
    DeadlineDaemonLastRunDatetime,
    QueuePosition,
)


def _sql_subtract_date(
    sql_session: Session,
    x: SQLColumnExpression[datetime],
    y: timedelta,
) -> SQLColumnExpression[datetime]:
    dialect_name = sql_session.get_bind().dialect.name
    if dialect_name == "sqlite":
        # SQLite does not support timedelta in queries
        return func.datetime(x, f"-{y.days} days")
    if dialect_name == "postgresql":
        return x - y
    raise NotImplementedError(
        f"Unsupported dialect: {dialect_name}",
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
) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing).where(
                _sql_subtract_date(
                    sql_session,
                    Borrowing.due_time,
                    timedelta(days=day),
                ).between(
                    last_run_datetime,
                    current_run_datetime,
                ),
            ),
        ).all(),
    )


def list_undelivered_overdue_borrowings(
    sql_session: Session,
    current_run_datetime: datetime,
) -> list[Borrowing]:
    return list(
        sql_session.scalars(
            select(Borrowing).where(
                Borrowing.due_time < current_run_datetime,
            ),
        ).all(),
    )


def list_newly_available_queue_items(
    sql_session: Session,
    last_run_datetime: datetime,
    current_run_datetime: datetime,
) -> list[QueuePosition]:
    items_returned_since_last_run = (
        select(BorrowingLog.fk_bookcase_item_uid)
        .where(
            BorrowingLog.event_type == BorrowingEventType.RETURNED,
            BorrowingLog.timestamp.between(last_run_datetime, current_run_datetime),
        )
        .distinct()
    )

    return list(
        sql_session.scalars(
            select(QueuePosition)
            .where(
                QueuePosition.notified_available_time.is_(None),
                QueuePosition.fk_bookcase_item_uid.in_(items_returned_since_last_run),
            )
            .order_by(QueuePosition.entered_queue_time)
            .group_by(QueuePosition.fk_bookcase_item_uid),
        ).all(),
    )


def list_expiring_queue_positions(
    sql_session: Session,
    last_run_datetime: datetime,
    current_run_datetime: datetime,
) -> list[QueuePosition]:
    return list(
        sql_session.scalars(
            select(QueuePosition).where(
                QueuePosition.notified_available_time.between(
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
) -> list[QueuePosition]:
    expiry_cutoff = current_run_datetime - timedelta(days=queue_position_expiry_days)
    return list(
        sql_session.scalars(
            select(QueuePosition).where(
                QueuePosition.notified_available_time < expiry_cutoff,
            ),
        ).all(),
    )


def find_next_queue_position(
    sql_session: Session,
    item_uid: int,
) -> QueuePosition | None:
    return sql_session.scalars(
        select(QueuePosition)
        .where(
            QueuePosition.fk_bookcase_item_uid == item_uid,
            QueuePosition.notified_available_time.is_(None),
        )
        .order_by(QueuePosition.entered_queue_time)
        .limit(1),
    ).one_or_none()
