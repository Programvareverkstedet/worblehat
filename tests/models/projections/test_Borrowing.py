from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseShelf,
    Borrowing,
    BorrowingEventType,
    BorrowingLog,
    MediaType,
)


def _make_bookcase_item(sql_session: Session) -> BookcaseItem:
    bookcase = Bookcase(name="Bookcase")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf])
    sql_session.flush()

    item = BookcaseItem("Some Book", "1234567890")
    item.media_type = MediaType.BOOK
    item.shelf = shelf
    sql_session.add(item)
    sql_session.flush()
    return item


def test_borrowed_renewed_returned_lifecycle(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    due_time = datetime.now() + timedelta(days=30)

    sql_session.add(BorrowingLog("alice", item, BorrowingEventType.BORROWED, due_time=due_time))
    sql_session.flush()

    borrowing = sql_session.get_one(Borrowing, (item.uid, "alice"))
    assert borrowing.due_time == due_time

    new_due_time = due_time + timedelta(days=30)
    sql_session.add(
        BorrowingLog("alice", item, BorrowingEventType.RENEWED, due_time=new_due_time),
    )
    sql_session.flush()
    sql_session.refresh(borrowing)
    assert borrowing.due_time == new_due_time

    sql_session.add(BorrowingLog("alice", item, BorrowingEventType.RETURNED))
    sql_session.flush()
    sql_session.expunge(borrowing)

    assert sql_session.get(Borrowing, (item.uid, "alice")) is None
