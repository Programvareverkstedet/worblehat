from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseItemBorrowingQueue,
    BookcaseShelf,
    MediaType,
)
from worblehat.queries.borrowing_queue import (
    is_in_borrowing_queue,
    list_all_queue_items,
    list_pending_queue_items_for_item,
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


def test_list_all_queue_items_orders_by_entered_queue_time(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    later = BookcaseItemBorrowingQueue("alice", item)
    later.entered_queue_time = datetime.now() + timedelta(hours=1)
    sooner = BookcaseItemBorrowingQueue("bob", item)
    sooner.entered_queue_time = datetime.now()
    sql_session.add_all([later, sooner])
    sql_session.flush()

    result = list_all_queue_items(sql_session)

    assert result == [sooner, later]


def test_is_in_borrowing_queue_true_when_present(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    sql_session.add(BookcaseItemBorrowingQueue("alice", item))
    sql_session.flush()

    assert is_in_borrowing_queue(sql_session, "alice", item) is True


def test_is_in_borrowing_queue_false_for_other_user(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    sql_session.add(BookcaseItemBorrowingQueue("alice", item))
    sql_session.flush()

    assert is_in_borrowing_queue(sql_session, "bob", item) is False


def test_is_in_borrowing_queue_false_when_empty(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    sql_session.add(item)
    sql_session.flush()

    assert is_in_borrowing_queue(sql_session, "alice", item) is False


def test_list_pending_queue_items_for_item_excludes_available_items(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    pending = BookcaseItemBorrowingQueue("alice", item)
    became_available = BookcaseItemBorrowingQueue("bob", item)
    became_available.item_became_available_time = datetime.now()
    sql_session.add_all([pending, became_available])
    sql_session.flush()

    result = list_pending_queue_items_for_item(sql_session, item)

    assert result == [pending]


def test_list_pending_queue_items_for_item_scopes_to_item(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    queue_item_a = BookcaseItemBorrowingQueue("alice", item_a)
    queue_item_b = BookcaseItemBorrowingQueue("bob", item_b)
    sql_session.add_all([queue_item_a, queue_item_b])
    sql_session.flush()

    result = list_pending_queue_items_for_item(sql_session, item_a)

    assert result == [queue_item_a]
