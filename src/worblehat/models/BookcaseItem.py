from __future__ import annotations

from typing import TYPE_CHECKING, Self

from sqlalchemy import (
    ForeignKey,
    SmallInteger,
    String,
    Text,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    WriteOnlyMapped,
    mapped_column,
    relationship,
)

from .Base import Base
from .enums import Language, LanguageSQL, MediaType, MediaTypeSQL
from .mixins import (
    UidMixin,
)
from .xref_tables import (
    Item_Author,
    Item_Category,
)

if TYPE_CHECKING:
    from .Author import Author
    from .BookcaseShelf import BookcaseShelf
    from .BorrowingLog import BorrowingLog
    from .Category import Category
    from .projections import Borrowing, QueuePosition
    from .QueueLog import QueueLog

from worblehat.flaskapp.database import db


class BookcaseItem(Base, UidMixin):
    isbn: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    owner: Mapped[str] = mapped_column(String, default="PVV")
    amount: Mapped[int] = mapped_column(SmallInteger, default=1)

    fk_bookcase_shelf_uid: Mapped[int] = mapped_column(ForeignKey("bookcase_shelf.uid"))
    media_type: Mapped[MediaType] = mapped_column(MediaTypeSQL)
    language: Mapped[Language | None] = mapped_column(LanguageSQL, default=None)

    shelf: Mapped[BookcaseShelf] = relationship(back_populates="items")

    borrowing_log: WriteOnlyMapped[BorrowingLog] = relationship(back_populates="item")
    queue_log: WriteOnlyMapped[QueueLog] = relationship(back_populates="item")

    borrowings: Mapped[set[Borrowing]] = relationship(back_populates="item")
    queue_positions: Mapped[set[QueuePosition]] = relationship(back_populates="item")

    categories: Mapped[set[Category]] = relationship(
        secondary=Item_Category.__table__,
        back_populates="items",
    )
    authors: Mapped[set[Author]] = relationship(
        secondary=Item_Author.__table__,
        back_populates="items",
    )

    def __init__(
        self,
        name: str,
        isbn: str | None = None,
        owner: str = "PVV",
    ) -> None:
        self.name = name
        self.isbn = isbn
        self.owner = owner

    @classmethod
    def get_by_isbn(cls, isbn: str, sql_session: Session = db.session) -> Self | None:
        """
        NOTE:
        This method defaults to using the flask_sqlalchemy session.
        It will not work outside of a request context, unless another session is provided.
        """
        return sql_session.execute(select(cls).where(cls.isbn == isbn)).scalar_one_or_none()
