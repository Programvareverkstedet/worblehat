from typing import Self

from flask import abort
from sqlalchemy import Integer, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import (
    Mapped,
    Session,
    mapped_column,
)

from worblehat.flaskapp.database import db


class UidMixin:
    uid: Mapped[int] = mapped_column(Integer, primary_key=True)

    @classmethod
    def get_by_uid(cls, uid: int, sql_session: Session = db.session) -> Self | None:
        """
        NOTE:
        This method defaults to using the flask_sqlalchemy session.
        It will not work outside of a request context, unless another session is provided.
        """
        return sql_session.execute(select(cls).where(cls.uid == uid)).scalar_one_or_none()

    @classmethod
    def get_by_uid_or_404(cls, uid: int, sql_session: Session = db.session) -> Self:
        """
        NOTE:
        This method defaults to using the flask_sqlalchemy session.
        It will not work outside of a request context, unless another session is provided.
        """
        try:
            return sql_session.execute(select(cls).where(cls.uid == uid)).scalar_one()
        except (NoResultFound, MultipleResultsFound):
            abort(404)
