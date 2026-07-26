from sqlalchemy.orm import Session

from worblehat.models import Bookcase, BookcaseShelf
from worblehat.queries.bookcase_shelf import (
    find_bookcase_shelf,
    list_bookcase_shelf_positions,
    list_bookcase_shelfs_ordered,
)


def test_find_bookcase_shelf_returns_match(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf])
    sql_session.flush()

    result = find_bookcase_shelf(sql_session, bookcase, column=0, row=0)

    assert result is shelf


def test_find_bookcase_shelf_returns_none_for_wrong_position(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf])
    sql_session.flush()

    assert find_bookcase_shelf(sql_session, bookcase, column=1, row=0) is None
    assert find_bookcase_shelf(sql_session, bookcase, column=0, row=1) is None


def test_find_bookcase_shelf_scopes_to_bookcase(sql_session: Session) -> None:
    bookcase_a = Bookcase(name="Bookcase A")
    bookcase_b = Bookcase(name="Bookcase B")
    shelf_a = BookcaseShelf(row=0, column=0, bookcase=bookcase_a)
    sql_session.add_all([bookcase_a, bookcase_b, shelf_a])
    sql_session.flush()

    assert find_bookcase_shelf(sql_session, bookcase_b, column=0, row=0) is None


def test_list_bookcase_shelfs_ordered(sql_session: Session) -> None:
    bookcase_b = Bookcase(name="Bookcase B")
    bookcase_a = Bookcase(name="Bookcase A")
    sql_session.add_all([bookcase_b, bookcase_a])
    sql_session.flush()

    shelf_b1 = BookcaseShelf(row=1, column=0, bookcase=bookcase_b)
    shelf_a2 = BookcaseShelf(row=0, column=2, bookcase=bookcase_a)
    shelf_a1 = BookcaseShelf(row=0, column=1, bookcase=bookcase_a)
    sql_session.add_all([shelf_b1, shelf_a2, shelf_a1])
    sql_session.flush()

    result = list_bookcase_shelfs_ordered(sql_session)

    assert result == [shelf_a1, shelf_a2, shelf_b1]


def test_list_bookcase_shelf_positions_returns_all_by_default(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A")
    shelf_1 = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    shelf_2 = BookcaseShelf(row=1, column=1, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf_1, shelf_2])
    sql_session.flush()

    result = list_bookcase_shelf_positions(sql_session, bookcase)

    assert set(result) == {(0, 0), (1, 1)}


def test_list_bookcase_shelf_positions_filters_by_column(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A")
    shelf_1 = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    shelf_2 = BookcaseShelf(row=1, column=1, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf_1, shelf_2])
    sql_session.flush()

    result = list_bookcase_shelf_positions(sql_session, bookcase, column=1)

    assert result == [(1, 1)]


def test_list_bookcase_shelf_positions_filters_by_row(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A")
    shelf_1 = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    shelf_2 = BookcaseShelf(row=1, column=1, bookcase=bookcase)
    sql_session.add_all([bookcase, shelf_1, shelf_2])
    sql_session.flush()

    result = list_bookcase_shelf_positions(sql_session, bookcase, row=1)

    assert result == [(1, 1)]
