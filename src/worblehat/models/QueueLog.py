from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
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
from .enums import QueueEventType, QueueEventTypeSQL
from .mixins import UidMixin

if TYPE_CHECKING:
    from .BookcaseItem import BookcaseItem


class QueueLog(Base, UidMixin):
    """
    Transaction log for all borrowing queue events.

    See the `QueueEventType` enum for the possible event types.
    """

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("BookcaseItem.uid"),
        index=True,
    )
    username: Mapped[str] = mapped_column(String, index=True)
    event_type: Mapped[QueueEventType] = mapped_column(QueueEventTypeSQL)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    item: Mapped[BookcaseItem] = relationship(back_populates="queue_log")

    __table_args__ = (
        Index(
            "ix_queuelog_item_user_uid",
            "fk_bookcase_item_uid",
            "username",
            "uid",
        ),
    )

    def __init__(
        self,
        username: str,
        item: BookcaseItem,
        event_type: QueueEventType,
        timestamp: datetime | None = None,
    ) -> None:
        self.username = username
        self.item = item
        self.event_type = event_type
        self.timestamp = timestamp if timestamp is not None else datetime.now()
