from datetime import datetime

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseShelf,
    BorrowingEventType,
    BorrowingLog,
    MediaType,
    QueueEventType,
    QueueLog,
    QueuePosition,
)


def _make_bookcase_item(sql_session: Session) -> BookcaseItem:
    media_type = MediaType(name="Book")
    bookcase = Bookcase(name="Bookcase")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([media_type, bookcase, shelf])
    sql_session.flush()

    item = BookcaseItem("Some Book", "1234567890")
    item.media_type = media_type
    item.shelf = shelf
    sql_session.add(item)
    sql_session.flush()
    return item


def test_joined_notified_expired_lifecycle(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)

    sql_session.add(QueueLog("alice", item, QueueEventType.JOINED))
    sql_session.flush()

    position = sql_session.get_one(QueuePosition, (item.uid, "alice"))
    assert position.notified_available_time is None

    notified_at = datetime.now()
    sql_session.add(QueueLog("alice", item, QueueEventType.NOTIFIED, timestamp=notified_at))
    sql_session.flush()
    sql_session.refresh(position)
    assert position.notified_available_time == notified_at

    sql_session.add(QueueLog("alice", item, QueueEventType.EXPIRED))
    sql_session.flush()
    sql_session.expunge(position)

    assert sql_session.get(QueuePosition, (item.uid, "alice")) is None


def test_claimed_removes_position(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)

    sql_session.add(QueueLog("alice", item, QueueEventType.JOINED))
    borrowed = BorrowingLog(
        "alice",
        item,
        BorrowingEventType.BORROWED,
        due_time=datetime.now(),
    )
    sql_session.add(borrowed)
    sql_session.flush()

    sql_session.add(
        QueueLog("alice", item, QueueEventType.CLAIMED, borrowing_log_entry=borrowed),
    )
    sql_session.flush()

    assert sql_session.get(QueuePosition, (item.uid, "alice")) is None
