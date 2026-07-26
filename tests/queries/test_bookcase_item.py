from sqlalchemy.orm import Session

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseShelf,
    MediaType,
)
from worblehat.queries.bookcase_item import (
    find_bookcase_item_by_isbn,
    find_bookcase_item_by_name,
    list_bookcase_items_by_owner,
    search_bookcase_item_owners,
    search_bookcase_items_by_title,
)


def _make_bookcase_item(
    sql_session: Session,
    name: str = "Some Book",
    isbn: str = "1234567890",
    owner: str = "PVV",
) -> BookcaseItem:
    media_type = MediaType(name=f"Media type for {name}")
    bookcase = Bookcase(name=f"Bookcase for {name}")
    shelf = BookcaseShelf(row=0, column=0, bookcase=bookcase)
    sql_session.add_all([media_type, bookcase, shelf])
    sql_session.flush()

    item = BookcaseItem(name, isbn, owner)
    item.media_type = media_type
    item.shelf = shelf
    sql_session.add(item)
    sql_session.flush()
    return item


def test_find_bookcase_item_by_isbn_returns_match(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session, isbn="1111111111")

    result = find_bookcase_item_by_isbn(sql_session, "1111111111")

    assert result is item


def test_find_bookcase_item_by_isbn_returns_none_when_missing(sql_session: Session) -> None:
    _make_bookcase_item(sql_session, isbn="1111111111")

    result = find_bookcase_item_by_isbn(sql_session, "2222222222")

    assert result is None


def test_find_bookcase_item_by_name_returns_match(sql_session: Session) -> None:
    item = _make_bookcase_item(sql_session, name="Unique Title")

    result = find_bookcase_item_by_name(sql_session, "Unique Title")

    assert result is item


def test_find_bookcase_item_by_name_returns_none_when_missing(sql_session: Session) -> None:
    _make_bookcase_item(sql_session, name="Unique Title")

    result = find_bookcase_item_by_name(sql_session, "Other Title")

    assert result is None


def test_search_bookcase_items_by_title_matches_substring_case_insensitively(
    sql_session: Session,
) -> None:
    item = _make_bookcase_item(sql_session, name="The Great Gatsby", isbn="1111111111")
    _make_bookcase_item(sql_session, name="Moby Dick", isbn="2222222222")

    result = search_bookcase_items_by_title(sql_session, "great gatsby")

    assert result == [item]


def test_search_bookcase_items_by_title_returns_empty_when_no_match(sql_session: Session) -> None:
    _make_bookcase_item(sql_session, name="The Great Gatsby")

    result = search_bookcase_items_by_title(sql_session, "nonexistent")

    assert result == []


def test_search_bookcase_item_owners_matches_substring_case_insensitively(
    sql_session: Session,
) -> None:
    _make_bookcase_item(sql_session, name="Book A", isbn="1111111111", owner="alice")
    _make_bookcase_item(sql_session, name="Book B", isbn="2222222222", owner="bob")

    result = search_bookcase_item_owners(sql_session, "ALI")

    assert result == ["alice"]


def test_search_bookcase_item_owners_returns_distinct_owners(sql_session: Session) -> None:
    _make_bookcase_item(sql_session, name="Book A", isbn="1111111111", owner="alice")
    _make_bookcase_item(sql_session, name="Book B", isbn="2222222222", owner="alice")

    result = search_bookcase_item_owners(sql_session, "ali")

    assert result == ["alice"]


def test_list_bookcase_items_by_owner_returns_only_matching_owner(sql_session: Session) -> None:
    item_a = _make_bookcase_item(sql_session, name="Book A", isbn="1111111111", owner="alice")
    _make_bookcase_item(sql_session, name="Book B", isbn="2222222222", owner="bob")

    result = list_bookcase_items_by_owner(sql_session, "alice")

    assert result == [item_a]
