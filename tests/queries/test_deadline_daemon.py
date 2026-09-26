from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseShelf,
    Borrowing,
    BorrowingEventType,
    BorrowingLog,
    DeadlineDaemonLastRunDatetime,
    MediaType,
    QueueEventType,
    QueueLog,
    QueuePosition,
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
    bookcase = Bookcase(name=f"Bookcase for {name}")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf])
    sql_session.flush()

    item = BookcaseItem(name, isbn)
    item.media_type = MediaType.BOOK
    item.shelf = shelf
    sql_session.add(item)
    sql_session.flush()
    return item


def _borrow(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    due_time: datetime | None = None,
    timestamp: datetime | None = None,
) -> Borrowing:
    """Appends a BORROWED log entry and returns the resulting `Borrowing` projection."""
    sql_session.add(
        BorrowingLog(
            username,
            item,
            BorrowingEventType.BORROWED,
            due_time=due_time if due_time is not None else datetime.now() + timedelta(days=30),
            timestamp=timestamp,
        ),
    )
    sql_session.flush()
    return sql_session.get_one(Borrowing, (item.uid, username))


def _return(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    timestamp: datetime | None = None,
) -> None:
    sql_session.add(BorrowingLog(username, item, BorrowingEventType.RETURNED, timestamp=timestamp))
    sql_session.flush()


def _join_queue(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    entered_queue_time: datetime | None = None,
) -> QueuePosition:
    """Appends a JOINED log entry and returns the resulting `QueuePosition` projection."""
    sql_session.add(QueueLog(username, item, QueueEventType.JOINED, timestamp=entered_queue_time))
    sql_session.flush()
    return sql_session.get_one(QueuePosition, (item.uid, username))


def _notify_queue(
    sql_session: Session,
    username: str,
    item: BookcaseItem,
    timestamp: datetime | None = None,
) -> None:
    sql_session.add(QueueLog(username, item, QueueEventType.NOTIFIED, timestamp=timestamp))
    sql_session.flush()


def _expire_queue(sql_session: Session, username: str, item: BookcaseItem) -> None:
    sql_session.add(QueueLog(username, item, QueueEventType.EXPIRED))
    sql_session.flush()


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

    close = _borrow(sql_session, "alice", item, due_time=now + timedelta(days=2))
    _borrow(sql_session, "bob", item, due_time=now + timedelta(days=20))

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

    _borrow(sql_session, "alice", item, due_time=now + timedelta(days=2))
    _return(sql_session, "alice", item, timestamp=now)

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

    overdue = _borrow(sql_session, "alice", item, due_time=now - timedelta(days=1))
    _borrow(sql_session, "bob", item, due_time=now + timedelta(days=1))
    _borrow(sql_session, "carol", item, due_time=now - timedelta(days=1))
    _return(sql_session, "carol", item, timestamp=now)

    result = list_undelivered_overdue_borrowings(sql_session, now)

    assert result == [overdue]


def test_list_newly_available_queue_items_requires_delivery_in_window(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    _borrow(sql_session, "alice", item)
    _return(sql_session, "alice", item, timestamp=now)
    queue_item = _join_queue(sql_session, "bob", item)

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

    _borrow(sql_session, "alice", item)
    _return(sql_session, "alice", item, timestamp=now - timedelta(days=10))
    _join_queue(sql_session, "bob", item)

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

    _borrow(sql_session, "alice", item)
    _join_queue(sql_session, "bob", item)

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

    _borrow(sql_session, "alice", item)
    _return(sql_session, "alice", item, timestamp=now)
    _join_queue(sql_session, "bob", item)
    _expire_queue(sql_session, "bob", item)

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == []


def test_list_newly_available_queue_items_returns_earliest_in_queue_when_multiple_queued(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    _borrow(sql_session, "alice", item)
    _return(sql_session, "alice", item, timestamp=now)

    first_in_line = _join_queue(
        sql_session,
        "bob",
        item,
        entered_queue_time=now - timedelta(days=2),
    )
    _join_queue(sql_session, "carol", item, entered_queue_time=now - timedelta(days=1))

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == [first_in_line]


def test_list_newly_available_queue_items_returns_one_per_item_when_multiple_items_have_queues(
    sql_session: Session,
) -> None:
    now = datetime.now()

    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111")
    _borrow(sql_session, "alice", item_a)
    _join_queue(sql_session, "carol", item_a, entered_queue_time=now - timedelta(days=1))
    _return(sql_session, "alice", item_a, timestamp=now)
    a_first_in_line = _join_queue(
        sql_session,
        "bob",
        item_a,
        entered_queue_time=now - timedelta(days=2),
    )

    item_b = _make_bookcase_item(sql_session, name="Book B", isbn="2222222222")
    _borrow(sql_session, "dave", item_b)
    _join_queue(sql_session, "frank", item_b, entered_queue_time=now - timedelta(days=1))
    _return(sql_session, "dave", item_b, timestamp=now)
    b_first_in_line = _join_queue(
        sql_session,
        "erin",
        item_b,
        entered_queue_time=now - timedelta(days=3),
    )

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert set(result) == {a_first_in_line, b_first_in_line}


def test_list_newly_available_queue_items_notifies_one_person_per_returned_copy(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    item.amount = 2
    sql_session.flush()

    _borrow(sql_session, "alice", item)
    _borrow(sql_session, "zoe", item)

    now = datetime.now()

    _return(sql_session, "alice", item, timestamp=now)
    _return(sql_session, "zoe", item, timestamp=now)

    first_in_line = _join_queue(
        sql_session,
        "bob",
        item,
        entered_queue_time=now - timedelta(days=3),
    )
    second_in_line = _join_queue(
        sql_session,
        "carol",
        item,
        entered_queue_time=now - timedelta(days=2),
    )
    third_in_line = _join_queue(
        sql_session,
        "dave",
        item,
        entered_queue_time=now - timedelta(days=1),
    )

    result = list_newly_available_queue_items(
        sql_session,
        last_run_datetime=now - timedelta(minutes=1),
        current_run_datetime=now + timedelta(minutes=1),
    )

    assert result == [first_in_line, second_in_line]
    assert third_in_line not in result


def test_list_expiring_queue_positions_matches_positions_in_window(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    in_window = _join_queue(sql_session, "alice", item)
    _notify_queue(sql_session, "alice", item, timestamp=now)

    out_of_window = _join_queue(sql_session, "bob", item)
    _notify_queue(sql_session, "bob", item, timestamp=now - timedelta(days=100))

    result = list_expiring_queue_positions(
        sql_session,
        last_run_datetime=now - timedelta(days=1),
        current_run_datetime=now + timedelta(days=1),
    )

    assert result == [in_window]


def test_list_overdue_queue_positions_matches_positions_older_than_expiry(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    overdue = _join_queue(sql_session, "alice", item)
    _notify_queue(sql_session, "alice", item, timestamp=now - timedelta(days=5))

    _join_queue(sql_session, "bob", item)
    _notify_queue(sql_session, "bob", item, timestamp=now)

    result = list_overdue_queue_positions(
        sql_session,
        queue_position_expiry_days=1,
        current_run_datetime=now,
    )

    assert result == [overdue]


def test_list_overdue_queue_positions_excludes_already_expired(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    _join_queue(sql_session, "alice", item)
    _notify_queue(sql_session, "alice", item, timestamp=now - timedelta(days=5))
    _expire_queue(sql_session, "alice", item)

    result = list_overdue_queue_positions(
        sql_session,
        queue_position_expiry_days=1,
        current_run_datetime=now,
    )

    assert result == []


def test_find_next_queue_position_returns_earliest_pending_entry(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    _join_queue(sql_session, "alice", item, entered_queue_time=now + timedelta(hours=1))
    sooner = _join_queue(sql_session, "bob", item, entered_queue_time=now)

    result = find_next_queue_position(sql_session, item.uid)

    assert result is sooner


def test_find_next_queue_position_skips_entries_that_already_became_available(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session)
    now = datetime.now()

    _join_queue(sql_session, "alice", item, entered_queue_time=now)
    _notify_queue(sql_session, "alice", item, timestamp=now)

    pending = _join_queue(sql_session, "bob", item, entered_queue_time=now + timedelta(hours=1))

    result = find_next_queue_position(sql_session, item.uid)

    assert result is pending


def test_find_next_queue_position_returns_none_when_empty(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session)

    result = find_next_queue_position(sql_session, item.uid)

    assert result is None
