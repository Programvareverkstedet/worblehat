from sqlalchemy import (
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from ..Base import Base
from ..mixins.XrefMixin import XrefMixin


class Item_Category(Base, XrefMixin):
    fk_item_uid: Mapped[int] = mapped_column(
        ForeignKey("bookcase_item.uid"),
        primary_key=True,
    )
    fk_category_uid: Mapped[int] = mapped_column(
        ForeignKey("category.uid"),
        primary_key=True,
    )
