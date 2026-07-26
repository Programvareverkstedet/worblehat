from sqlalchemy.orm import Session

from worblehat.models import Bookcase
from worblehat.queries.bookcase import find_bookcase_by_name


def test_find_bookcase_by_name_returns_match(sql_session: Session) -> None:
    bookcase = Bookcase(name="Bookcase A", description="A bookcase")
    sql_session.add(bookcase)
    sql_session.flush()

    result = find_bookcase_by_name(sql_session, "Bookcase A")

    assert result is bookcase


def test_find_bookcase_by_name_is_case_sensitive(sql_session: Session) -> None:
    sql_session.add(Bookcase(name="Bookcase A"))
    sql_session.flush()

    result = find_bookcase_by_name(sql_session, "bookcase a")

    assert result is None
