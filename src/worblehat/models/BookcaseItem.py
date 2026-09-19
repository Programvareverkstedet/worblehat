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
    from .Language import Language
    from .MediaType import MediaType
    from .projections import Borrowing, QueuePosition
    from .QueueLog import QueueLog

from worblehat.flaskapp.database import db


class BookcaseItem(Base, UidMixin):
    isbn: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    owner: Mapped[str] = mapped_column(String, default="PVV")
    amount: Mapped[int] = mapped_column(SmallInteger, default=1)

    fk_media_type_uid: Mapped[int] = mapped_column(ForeignKey("media_type.uid"))
    fk_bookcase_shelf_uid: Mapped[int] = mapped_column(ForeignKey("bookcase_shelf.uid"))
    fk_language_uid: Mapped[int | None] = mapped_column(ForeignKey("language.uid"))

    media_type: Mapped[MediaType] = relationship(back_populates="items")
    shelf: Mapped[BookcaseShelf] = relationship(back_populates="items")
    language: Mapped[Language] = relationship()

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
