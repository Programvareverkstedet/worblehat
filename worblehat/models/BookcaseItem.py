from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import (
  ForeignKey,
  Integer,
  SmallInteger,
  String,
  Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .Base import Base
from .mixins import (
    UidMixin,
    UniqueNameMixin,
)
from .xref_tables import (
    Item_Category,
    Item_Author,
)
if TYPE_CHECKING:
    from .Author import Author
    from .BookcaseItemBorrowing import BookcaseItemBorrowing
    from .BookcaseItemBorrowingQueue import BookcaseItemBorrowingQueue
    from .BookcaseShelf import BookcaseShelf
    from .Category import Category
    from .Language import Language
    from .MediaType import MediaType

from worblehat.flaskapp.database import db

class BookcaseItem(Base, UidMixin):
    isbn: Mapped[int] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, index=True)
    owner: Mapped[str] = mapped_column(String, default='PVV')
    amount: Mapped[int] = mapped_column(SmallInteger, default=1)

    fk_media_type_uid: Mapped[int] = mapped_column(ForeignKey('MediaType.uid'))
    fk_bookcase_shelf_uid: Mapped[int | None] = mapped_column(ForeignKey('BookcaseShelf.uid'))
    fk_language_uid: Mapped[int | None] = mapped_column(ForeignKey('Language.uid'))

    media_type: Mapped[MediaType] = relationship(back_populates='items')
    shelf: Mapped[BookcaseShelf] = relationship(back_populates='items')
    language: Mapped[Language] = relationship()
    borrowings: Mapped[set[BookcaseItemBorrowing]] = relationship(back_populates='item')
    borrowing_queue: Mapped[set[BookcaseItemBorrowingQueue]] = relationship(back_populates='item')

    categories: Mapped[set[Category]] = relationship(
        secondary = Item_Category.__table__,
        back_populates = 'items',
    )
    authors: Mapped[set[Author]] = relationship(
        secondary = Item_Author.__table__,
        back_populates = 'items',
    )

    def __init__(
        self,
        name: str,
        isbn: int | None = None,
        owner: str = 'PVV',
    ):
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
        return sql_session.query(cls).where(cls.isbn == isbn).one_or_none()