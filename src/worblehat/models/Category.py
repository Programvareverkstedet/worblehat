from __future__ import annotations
from typing import TYPE_CHECKING

from sqlalchemy import Text
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
from .xref_tables import Item_Category
if TYPE_CHECKING:
    from .BookcaseItem import BookcaseItem

class Category(Base, UidMixin, UniqueNameMixin):
    description: Mapped[str | None] = mapped_column(Text)

    items: Mapped[set[BookcaseItem]] = relationship(
        secondary=Item_Category.__table__,
        back_populates='categories',
    )

    def __init__(
        self,
        name: str,
        description: str | None = None,
    ):
        self.name = name
        self.description = description