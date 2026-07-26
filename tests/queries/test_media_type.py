import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from worblehat.models import MediaType
from worblehat.queries.media_type import find_media_type_by_name


def test_find_media_type_by_name_returns_match_case_insensitively(sql_session: Session) -> None:
    book = MediaType(name="Book", description="A physical book")
    comic = MediaType(name="Comic", description="A comic book")
    sql_session.add_all([book, comic])
    sql_session.flush()

    result = find_media_type_by_name(sql_session, "book")

    assert result is book


def test_find_media_type_by_name_raises_when_missing(sql_session: Session) -> None:
    sql_session.add(MediaType(name="Comic"))
    sql_session.flush()

    with pytest.raises(NoResultFound):
        find_media_type_by_name(sql_session, "book")
