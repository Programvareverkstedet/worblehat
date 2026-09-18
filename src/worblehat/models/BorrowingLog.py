from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from .Base import Base
from .enums import BorrowingEventType, BorrowingEventTypeSQL
from .mixins import UidMixin

if TYPE_CHECKING:
    from .BookcaseItem import BookcaseItem


class BorrowingLog(Base, UidMixin):
    """
    Transaction log for all borrow events.

    See the `BorrowingEventType` enum for the possible event types.
    See also the `Borrowing` projection.
    """

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("BookcaseItem.uid"),
        index=True,
    )
    username: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[BorrowingEventType] = mapped_column(BorrowingEventTypeSQL)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    due_time: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    item: Mapped[BookcaseItem] = relationship(back_populates="borrowing_log")

    __table_args__ = (
        CheckConstraint(
            f"(event_type = '{BorrowingEventType.RETURNED.value}') = (due_time IS NULL)",
            name="due_time_set_iff_not_returned",
        ),
        Index(
            "ix_borrowinglog_item_user_uid",
            "fk_bookcase_item_uid",
            "username",
            "uid",
        ),
    )

    def __init__(
        self,
        username: str,
        item: BookcaseItem,
        event_type: BorrowingEventType,
        due_time: datetime | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        self.username = username
        self.item = item
        self.event_type = event_type
        self.due_time = due_time
        self.timestamp = timestamp if timestamp is not None else datetime.now()
