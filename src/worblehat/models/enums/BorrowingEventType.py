from enum import StrEnum, auto

from sqlalchemy import Enum as SQLEnum


class BorrowingEventType(StrEnum):
    """
    Event types for `BorrowingLog`.
    """

    BORROWED = auto()
    """Item borrowed, due_time set to the new deadline"""

    RENEWED = auto()
    """Loan extended, due_time set to the new deadline"""

    RETURNED = auto()
    """Item given back, due_time null"""


BorrowingEventTypeSQL = SQLEnum(
    BorrowingEventType,
    native_enum=True,
    create_constraint=True,
    validate_strings=True,
    values_callable=lambda x: [i.value for i in x],
)
