from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import Author


def search_authors_by_name(sql_session: Session, text: str) -> list[Author]:
    return list(
        sql_session.scalars(
            select(Author).where(Author.name.ilike(f"%{text}%")),
        ).all(),
    )
