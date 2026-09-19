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
from .enums import BorrowingEventType, QueueEventType, QueueEventTypeSQL
from .mixins import UidMixin

if TYPE_CHECKING:
    from .BookcaseItem import BookcaseItem
    from .BorrowingLog import BorrowingLog


class QueueLog(Base, UidMixin):
    """
    Transaction log for all borrowing queue events.

    See the `QueueEventType` enum for the possible event types.
    See also the `QueuePosition` projection.
    """

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("bookcase_item.uid"),
        index=True,
    )
    username: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[QueueEventType] = mapped_column(QueueEventTypeSQL)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Only set on CLAIMED, pointing at the corresponding BORROWED entry in
    # the BorrowingLog.
    fk_borrowing_log_uid: Mapped[int | None] = mapped_column(
        ForeignKey("borrowing_log.uid"),
        default=None,
    )

    item: Mapped[BookcaseItem] = relationship(back_populates="queue_log")
    borrowing_log_entry: Mapped[BorrowingLog | None] = relationship()

    __table_args__ = (
        Index(
            "ix_queuelog_item_user_uid",
            "fk_bookcase_item_uid",
            "username",
            "uid",
        ),
        CheckConstraint(
            f"(event_type = '{QueueEventType.CLAIMED.value}') = (fk_borrowing_log_uid IS NOT NULL)",
            name="borrowing_log_fk_set_iff_claimed",
        ),
    )

    def __init__(
        self,
        username: str,
        item: BookcaseItem,
        event_type: QueueEventType,
        borrowing_log_entry: BorrowingLog | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        if (event_type == QueueEventType.CLAIMED) != (borrowing_log_entry is not None):
            raise ValueError(
                "borrowing_log_entry must be given if and only if event_type is CLAIMED",
            )
        if borrowing_log_entry is not None and (
            borrowing_log_entry.event_type != BorrowingEventType.BORROWED
        ):
            raise ValueError("borrowing_log_entry must be a BORROWED entry")

        self.username = username
        self.item = item
        self.event_type = event_type
        self.borrowing_log_entry = borrowing_log_entry
        self.timestamp = timestamp if timestamp is not None else datetime.now()
