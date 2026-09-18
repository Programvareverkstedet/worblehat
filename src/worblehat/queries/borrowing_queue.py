from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from worblehat.models import BookcaseItem, BorrowingLog, QueueEventType, QueueLog, QueuePosition
from worblehat.queries.borrowing import has_active_borrowing


def list_all_queue_items(sql_session: Session) -> list[QueuePosition]:
    return list(
        sql_session.scalars(
            select(QueuePosition).order_by(
                QueuePosition.entered_queue_time,
            ),
        ).all(),
    )


def get_queue_position(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
) -> QueuePosition | None:
    return sql_session.scalars(
        select(QueuePosition).where(
            QueuePosition.username == username,
            QueuePosition.fk_bookcase_item_uid == item.uid,
        ),
    ).one_or_none()


def is_in_borrowing_queue(sql_session: Session, username: str, item: BookcaseItem) -> bool:
    return sql_session.scalar(
        select(
            exists().where(
                QueuePosition.username == username,
                QueuePosition.fk_bookcase_item_uid == item.uid,
            ),
        ),
    )


def list_queue_positions_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[QueuePosition]:
    return list(
        sql_session.scalars(
            select(QueuePosition)
            .where(QueuePosition.fk_bookcase_item_uid == item.uid)
            .order_by(QueuePosition.entered_queue_time),
        ).all(),
    )


def list_pending_queue_items_for_item(
    sql_session: Session,
    item: BookcaseItem,
) -> list[QueuePosition]:
    return list(
        sql_session.scalars(
            select(QueuePosition)
            .where(
                QueuePosition.fk_bookcase_item_uid == item.uid,
                QueuePosition.notified_available_time.is_(None),
            )
            .order_by(QueuePosition.entered_queue_time),
        ).all(),
    )


def list_queue_log_for_item(sql_session: Session, item: BookcaseItem) -> list[QueueLog]:
    return list(
        sql_session.scalars(
            select(QueueLog)
            .where(QueueLog.fk_bookcase_item_uid == item.uid)
            .order_by(QueueLog.uid),
        ).all(),
    )


def join_borrowing_queue(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    _unsafe: bool = False,
) -> QueuePosition:
    if not _unsafe:
        if has_active_borrowing(sql_session, username, item):
            raise ValueError(f"{username} already has an active borrowing of this item")
        if is_in_borrowing_queue(sql_session, username, item):
            raise ValueError(f"{username} is already queued for this item")

    sql_session.add(QueueLog(username, item, QueueEventType.JOINED))
    sql_session.flush()
    return sql_session.get_one(QueuePosition, (item.uid, username))


def leave_borrowing_queue(
    sql_session: Session,
    position: QueuePosition,
    _unsafe: bool = False,
) -> None:
    if not _unsafe and not is_in_borrowing_queue(sql_session, position.username, position.item):
        raise ValueError(f"{position.username} is not currently queued for this item")

    sql_session.add(QueueLog(position.username, position.item, QueueEventType.LEFT))
    sql_session.flush()
    sql_session.expunge(position)


def claim_borrowing_queue_position(
    sql_session: Session,
    position: QueuePosition,
    borrowing_log_entry: BorrowingLog,
    _unsafe: bool = False,
) -> None:
    if not _unsafe:
        if not is_in_borrowing_queue(sql_session, position.username, position.item):
            raise ValueError(f"{position.username} is not currently queued for this item")
        if (
            borrowing_log_entry.username != position.username
            or borrowing_log_entry.fk_bookcase_item_uid != position.fk_bookcase_item_uid
        ):
            raise ValueError("borrowing_log_entry does not belong to this queue position")

    sql_session.add(
        QueueLog(
            position.username,
            position.item,
            QueueEventType.CLAIMED,
            borrowing_log_entry=borrowing_log_entry,
        ),
    )
    sql_session.flush()
    sql_session.expunge(position)


def expire_borrowing_queue_position(
    sql_session: Session,
    position: QueuePosition,
    _unsafe: bool = False,
) -> None:
    if not _unsafe and not is_in_borrowing_queue(sql_session, position.username, position.item):
        raise ValueError(f"{position.username} is not currently queued for this item")

    sql_session.add(QueueLog(position.username, position.item, QueueEventType.EXPIRED))
    sql_session.flush()
    sql_session.expunge(position)


def notify_borrowing_queue_position(
    sql_session: Session,
    position: QueuePosition,
    notified_at: datetime | None = None,
    _unsafe: bool = False,
) -> QueuePosition:
    if not _unsafe:
        if not is_in_borrowing_queue(sql_session, position.username, position.item):
            raise ValueError(f"{position.username} is not currently queued for this item")
        if position.notified_available_time is not None:
            raise ValueError(f"{position.username}'s queue position has already been notified")

    sql_session.add(
        QueueLog(
            position.username,
            position.item,
            QueueEventType.NOTIFIED,
            timestamp=notified_at,
        ),
    )
    sql_session.flush()
    sql_session.refresh(position)
    return position
