from enum import StrEnum, auto

from sqlalchemy import Enum as SQLEnum


class MediaType(StrEnum):
    BOARD_GAME = auto()
    BOOK = auto()
    COMIC = auto()
    MOVIE = auto()
    VIDEO_GAME = auto()


MediaTypeSQL = SQLEnum(
    MediaType,
    native_enum=True,
    create_constraint=True,
    validate_strings=True,
    values_callable=lambda x: [i.value for i in x],
)
