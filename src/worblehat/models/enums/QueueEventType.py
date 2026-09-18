from enum import StrEnum, auto

from sqlalchemy import Enum as SQLEnum


class QueueEventType(StrEnum):
    """
    Event types for `QueueLog`.
    """

    JOINED = auto()
    """User entered the queue for an unavailable item"""

    LEFT = auto()
    """User voluntarily left the queue before it was their turn"""

    NOTIFIED = auto()
    """Item became available, grace period to claim it started"""

    EXPIRED = auto()
    """Grace period lapsed without the item being claimed"""

    CLAIMED = auto()
    """User borrowed the item, leaving the queue as a result"""


QueueEventTypeSQL = SQLEnum(
    QueueEventType,
    native_enum=True,
    create_constraint=True,
    validate_strings=True,
    values_callable=lambda x: [i.value for i in x],
)
