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
from worblehat.queries.borrowing import (
    has_active_borrowing,
    list_active_borrowings,
    list_active_borrowings_for_item,
    list_borrowings_for_isbn,
    list_overdue_borrowings,
)


def _make_bookcase_item(
    sql_session: Session,
    name: str = "Some Book",
    isbn: str = "1234567890",
) -> BookcaseItem:
    """Creates a BookcaseItem along with the MediaType/Bookcase/BookcaseShelf it needs."""
    media_type = MediaType(name=f"Media type for {name}")
    bookcase = Bookcase(name=f"Bookcase for {name}")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([media_type, bookcase, shelf])
    sql_session.flush()

    item = BookcaseItem(name, isbn)
    item.media_type = media_type
    item.shelf = shelf
    sql_session.add(item)
    sql_session.flush()
    return item


def _borrow(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    due_time: datetime | None = None,
) -> Borrowing:
    sql_session.add(
        BorrowingLog(
            username,
            item,
            BorrowingEventType.BORROWED,
            due_time=due_time if due_time is not None else datetime.now() + timedelta(days=30),
        ),
    )
    sql_session.flush()
    return sql_session.get_one(Borrowing, (item.uid, username))


def _return(sql_session: Session, username: str, item: BookcaseItem) -> None:
    sql_session.add(BorrowingLog(username, item, BorrowingEventType.RETURNED))
    sql_session.flush()


def test_list_active_borrowings_excludes_delivered(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    active = _borrow(sql_session, "alice", item)
    _borrow(sql_session, "bob", item)
    _return(sql_session, "bob", item)

    result = list_active_borrowings(sql_session)

    assert result == [active]


def test_list_active_borrowings_orders_by_due_time(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    later = _borrow(sql_session, "alice", item, due_time=datetime.now() + timedelta(days=10))
    sooner = _borrow(sql_session, "bob", item, due_time=datetime.now() + timedelta(days=1))

    result = list_active_borrowings(sql_session)

    assert result == [sooner, later]


def test_list_active_borrowings_for_item_scopes_to_item(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    borrowing_a = _borrow(sql_session, "alice", item_a)
    _borrow(sql_session, "bob", item_b)

    result = list_active_borrowings_for_item(sql_session, item_a)

    assert result == [borrowing_a]


def test_has_active_borrowing_true_when_undelivered_borrowing_exists(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    _borrow(sql_session, "alice", item)

    assert has_active_borrowing(sql_session, "alice", item) is True


def test_has_active_borrowing_false_when_delivered(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    _borrow(sql_session, "alice", item)
    _return(sql_session, "alice", item)

    assert has_active_borrowing(sql_session, "alice", item) is False


def test_has_active_borrowing_false_for_other_user(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    _borrow(sql_session, "alice", item)

    assert has_active_borrowing(sql_session, "bob", item) is False


def test_list_borrowings_for_isbn_scopes_to_isbn(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    borrowing_a = _borrow(sql_session, "alice", item_a)
    _borrow(sql_session, "bob", item_b)

    result = list_borrowings_for_isbn(sql_session, "1111111111")

    assert result == [borrowing_a]


def test_list_borrowings_for_isbn_orders_by_username(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    borrowing_bob = _borrow(sql_session, "bob", item)
    borrowing_alice = _borrow(sql_session, "alice", item)

    result = list_borrowings_for_isbn(sql_session, item.isbn)

    assert result == [borrowing_alice, borrowing_bob]


def test_list_overdue_borrowings_only_returns_undelivered_past_deadline(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)

    overdue = _borrow(sql_session, "alice", item, due_time=datetime.now() - timedelta(days=1))
    _borrow(sql_session, "bob", item, due_time=datetime.now() + timedelta(days=1))
    _borrow(sql_session, "carol", item, due_time=datetime.now() - timedelta(days=1))
    _return(sql_session, "carol", item)

    result = list_overdue_borrowings(sql_session)

    assert result == [overdue]
