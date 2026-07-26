from sqlalchemy.orm import Session

from worblehat.models import Author
from worblehat.queries.author import search_authors_by_name


def test_search_authors_by_name_matches_substring_case_insensitively(sql_session: Session) -> None:
    tolkien = Author(name="J.R.R. Tolkien")
    orwell = Author(name="George Orwell")
    sql_session.add_all([tolkien, orwell])
    sql_session.flush()

    result = search_authors_by_name(sql_session, "tolkien")

    assert result == [tolkien]


def test_search_authors_by_name_returns_empty_when_no_match(sql_session: Session) -> None:
    sql_session.add(Author(name="Roald Dahl"))
    sql_session.flush()

    result = search_authors_by_name(sql_session, "nonexistent")

    assert result == []


def test_search_authors_by_name_returns_all_matches(sql_session: Session) -> None:
    tolkien = Author(name="J.R.R. Tolkien")
    orwell = Author(name="George Orwell")
    dahl = Author(name="Roald Dahl")
    nesbo = Author(name="Jo Nesbø")
    nakamura = Author(name="中村 文則")
    sql_session.add_all([tolkien, orwell, dahl, nesbo, nakamura])
    sql_session.flush()

    result = search_authors_by_name(sql_session, "e")

    assert set(result) == {tolkien, orwell, nesbo}
