from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .Base import Base
from .mixins import UidMixin

if TYPE_CHECKING:
    from .BookcaseItem import BookcaseItem


class BookcaseItemBorrowing(Base, UidMixin):
    username: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now())
    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now() + timedelta(days=30),
    )
    delivered: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("BookcaseItem.uid"),
        index=True,
    )

    item: Mapped[BookcaseItem] = relationship(back_populates="borrowings")

    def __init__(
        self,
        username: str,
        item: BookcaseItem,
    ) -> None:
        self.username = username
        self.item = item
        self.start_time = datetime.now()
        self.end_time = datetime.now() + timedelta(days=30)
