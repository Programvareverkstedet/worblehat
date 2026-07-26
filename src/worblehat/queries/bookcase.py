from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import Bookcase


def find_bookcase_by_name(sql_session: Session, name: str) -> Bookcase | None:
    return sql_session.scalars(
        select(Bookcase).where(Bookcase.name == name),
    ).one_or_none()
