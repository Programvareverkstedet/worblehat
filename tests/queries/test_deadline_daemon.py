from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseItemBorrowing,
    BookcaseItemBorrowingQueue,
    BookcaseShelf,
    DeadlineDaemonLastRunDatetime,
    MediaType,
)
from worblehat.queries.deadline_daemon import (
    find_last_run,
    find_next_queue_position,
    list_close_deadline_borrowings,
    list_expiring_queue_positions,
    list_newly_available_queue_items,
    list_overdue_queue_positions,
    list_undelivered_overdue_borrowings,
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


def test_find_last_run_returns_none_when_db_is_empty(sql_session: Session) -> None:
    assert find_last_run(sql_session) is None


def test_find_last_run_returns_the_single_row(sql_session: Session) -> None:
    last_run = DeadlineDaemonLastRunDatetime(time=datetime.now())
    sql_session.add(last_run)
    sql_session.flush()

    assert find_last_run(sql_session) is last_run


def test_list_close_deadline_borrowings_matches_borrowings_ending_in_n_days(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    close = BookcaseItemBorrowing("alice", item)
    close.end_time = now + timedelta(days=2)

    far = BookcaseItemBorrowing("bob", item)
    far.end_time = now + timedelta(days=20)

    sql_session.add_all([close, far])
    sql_session.flush()

    result = list_close_deadline_borrowings(
        sql_session,
        day=2,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == [close]


def test_list_close_deadline_borrowings_excludes_delivered(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    delivered = BookcaseItemBorrowing("alice", item)
    delivered.end_time = now + timedelta(days=2)
    delivered.delivered = now

    sql_session.add(delivered)
    sql_session.flush()

    result = list_close_deadline_borrowings(
        sql_session,
        day=2,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == []


def test_list_undelivered_overdue_borrowings_only_returns_undelivered_past_deadline(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    overdue = BookcaseItemBorrowing("alice", item)
    overdue.end_time = now - timedelta(days=1)

    not_yet_due = BookcaseItemBorrowing("bob", item)
    not_yet_due.end_time = now + timedelta(days=1)

    overdue_but_delivered = BookcaseItemBorrowing("carol", item)
    overdue_but_delivered.end_time = now - timedelta(days=1)
    overdue_but_delivered.delivered = now

    sql_session.add_all([overdue, not_yet_due, overdue_but_delivered])
    sql_session.flush()

    result = list_undelivered_overdue_borrowings(sql_session, now)

    assert result == [overdue]


def test_list_newly_available_queue_items_requires_delivery_in_window(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    borrowing = BookcaseItemBorrowing("alice", item)
    borrowing.delivered = now
    queue_item = BookcaseItemBorrowingQueue("bob", item)

    sql_session.add_all([borrowing, queue_item])
    sql_session.flush()

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == [queue_item]


def test_list_newly_available_queue_items_excludes_delivery_outside_window(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    borrowing = BookcaseItemBorrowing("alice", item)
    borrowing.delivered = now - timedelta(days=10)
    queue_item = BookcaseItemBorrowingQueue("bob", item)

    sql_session.add_all([borrowing, queue_item])
    sql_session.flush()

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == []


def test_list_newly_available_queue_items_excludes_undelivered_borrowings(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    borrowing = BookcaseItemBorrowing("alice", item)
    queue_item = BookcaseItemBorrowingQueue("bob", item)

    sql_session.add_all([borrowing, queue_item])
    sql_session.flush()

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == []


def test_list_newly_available_queue_items_excludes_expired_queue_entries(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    borrowing = BookcaseItemBorrowing("alice", item)
    borrowing.delivered = now
    queue_item = BookcaseItemBorrowingQueue("bob", item)
    queue_item.expired = True

    sql_session.add_all([borrowing, queue_item])
    sql_session.flush()

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == []


def test_list_expiring_queue_positions_matches_positions_in_window(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    sql_session.add(BookcaseItemBorrowing("someone", item))

    in_window = BookcaseItemBorrowingQueue("alice", item)
    in_window.item_became_available_time = now

    out_of_window = BookcaseItemBorrowingQueue("bob", item)
    out_of_window.item_became_available_time = now - timedelta(days=100)

    sql_session.add_all([in_window, out_of_window])
    sql_session.flush()

    result = list_expiring_queue_positions(
        sql_session,
        last_run_datetime=now - timedelta(days=1),
        current_run_datetime=now + timedelta(days=1),
    )

    assert result == [in_window]


def test_list_expiring_queue_positions_ignores_items_without_a_borrowing(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    queue_item = BookcaseItemBorrowingQueue("alice", item)
    queue_item.item_became_available_time = now
    sql_session.add(queue_item)
    sql_session.flush()

    result = list_expiring_queue_positions(
        sql_session,
        last_run_datetime=now - timedelta(days=1),
        current_run_datetime=now + timedelta(days=1),
    )

    assert result == []


def test_list_overdue_queue_positions_matches_positions_older_than_expiry(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    overdue = BookcaseItemBorrowingQueue("alice", item)
    overdue.item_became_available_time = now - timedelta(days=5)

    not_overdue = BookcaseItemBorrowingQueue("bob", item)
    not_overdue.item_became_available_time = now

    sql_session.add_all([overdue, not_overdue])
    sql_session.flush()

    result = list_overdue_queue_positions(
        sql_session,
        queue_position_expiry_days=1,
        current_run_datetime=now,
    )

    assert result == [overdue]


def test_list_overdue_queue_positions_excludes_already_expired(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    already_expired = BookcaseItemBorrowingQueue("alice", item)
    already_expired.item_became_available_time = now - timedelta(days=5)
    already_expired.expired = True

    sql_session.add(already_expired)
    sql_session.flush()

    result = list_overdue_queue_positions(
        sql_session,
        queue_position_expiry_days=1,
        current_run_datetime=now,
    )

    assert result == []


def test_find_next_queue_position_returns_earliest_pending_entry(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    later = BookcaseItemBorrowingQueue("alice", item)
    later.entered_queue_time = now + timedelta(hours=1)
    sooner = BookcaseItemBorrowingQueue("bob", item)
    sooner.entered_queue_time = now

    sql_session.add_all([later, sooner])
    sql_session.flush()

    result = find_next_queue_position(sql_session, item.uid)

    assert result is sooner


def test_find_next_queue_position_skips_entries_that_already_became_available(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    already_available = BookcaseItemBorrowingQueue("alice", item)
    already_available.entered_queue_time = now
    already_available.item_became_available_time = now

    pending = BookcaseItemBorrowingQueue("bob", item)
    pending.entered_queue_time = now + timedelta(hours=1)

    sql_session.add_all([already_available, pending])
    sql_session.flush()

    result = find_next_queue_position(sql_session, item.uid)

    assert result is pending


def test_find_next_queue_position_returns_none_when_empty(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)

    result = find_next_queue_position(sql_session, item.uid)

    assert result is None
