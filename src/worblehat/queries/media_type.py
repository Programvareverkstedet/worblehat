from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import MediaType


def find_media_type_by_name(sql_session: Session, name: str) -> MediaType:
    return sql_session.scalars(
        select(MediaType).where(MediaType.name.ilike(name)),
    ).one()
