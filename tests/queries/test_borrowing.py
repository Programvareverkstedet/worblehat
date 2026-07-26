from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseItemBorrowing,
    BookcaseShelf,
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


def test_list_active_borrowings_excludes_delivered(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    active = BookcaseItemBorrowing("alice", item)
    delivered = BookcaseItemBorrowing("bob", item)
    delivered.delivered = datetime.now()
    sql_session.add_all([active, delivered])
    sql_session.flush()

    result = list_active_borrowings(sql_session)

    assert result == [active]


def test_list_active_borrowings_orders_by_end_time(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    later = BookcaseItemBorrowing("alice", item)
    later.end_time = datetime.now() + timedelta(days=10)
    sooner = BookcaseItemBorrowing("bob", item)
    sooner.end_time = datetime.now() + timedelta(days=1)
    sql_session.add_all([later, sooner])
    sql_session.flush()

    result = list_active_borrowings(sql_session)

    assert result == [sooner, later]


def test_list_active_borrowings_for_item_scopes_to_item(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    borrowing_a = BookcaseItemBorrowing("alice", item_a)
    borrowing_b = BookcaseItemBorrowing("bob", item_b)
    sql_session.add_all([borrowing_a, borrowing_b])
    sql_session.flush()

    result = list_active_borrowings_for_item(sql_session, item_a)

    assert result == [borrowing_a]


def test_has_active_borrowing_true_when_undelivered_borrowing_exists(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    sql_session.add(BookcaseItemBorrowing("alice", item))
    sql_session.flush()

    assert has_active_borrowing(sql_session, "alice", item) is True


def test_has_active_borrowing_false_when_delivered(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    borrowing = BookcaseItemBorrowing("alice", item)
    borrowing.delivered = datetime.now()
    sql_session.add(borrowing)
    sql_session.flush()

    assert has_active_borrowing(sql_session, "alice", item) is False


def test_has_active_borrowing_false_for_other_user(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    sql_session.add(BookcaseItemBorrowing("alice", item))
    sql_session.flush()

    assert has_active_borrowing(sql_session, "bob", item) is False


def test_list_borrowings_for_isbn_scopes_to_isbn(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    borrowing_a = BookcaseItemBorrowing("alice", item_a)
    borrowing_b = BookcaseItemBorrowing("bob", item_b)
    sql_session.add_all([borrowing_a, borrowing_b])
    sql_session.flush()

    result = list_borrowings_for_isbn(sql_session, "1111111111")

    assert result == [borrowing_a]


def test_list_borrowings_for_isbn_orders_by_username(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    borrowing_bob = BookcaseItemBorrowing("bob", item)
    borrowing_alice = BookcaseItemBorrowing("alice", item)
    sql_session.add_all([borrowing_bob, borrowing_alice])
    sql_session.flush()

    result = list_borrowings_for_isbn(sql_session, item.isbn)

    assert result == [borrowing_alice, borrowing_bob]


def test_list_overdue_borrowings_only_returns_undelivered_past_deadline(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)

    overdue = BookcaseItemBorrowing("alice", item)
    overdue.end_time = datetime.now() - timedelta(days=1)

    not_yet_due = BookcaseItemBorrowing("bob", item)
    not_yet_due.end_time = datetime.now() + timedelta(days=1)

    overdue_but_delivered = BookcaseItemBorrowing("carol", item)
    overdue_but_delivered.end_time = datetime.now() - timedelta(days=1)
    overdue_but_delivered.delivered = datetime.now()

    sql_session.add_all([overdue, not_yet_due, overdue_but_delivered])
    sql_session.flush()

    result = list_overdue_borrowings(sql_session)

    assert result == [overdue]
