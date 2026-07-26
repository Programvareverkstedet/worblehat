from sqlalchemy import select
from sqlalchemy.orm import Session

from worblehat.models import BookcaseItem


def find_bookcase_item_by_isbn(sql_session: Session, isbn: str) -> BookcaseItem | None:
    return sql_session.scalars(
        select(BookcaseItem).where(BookcaseItem.isbn == isbn),
    ).one_or_none()


def find_bookcase_item_by_name(sql_session: Session, name: str) -> BookcaseItem | None:
    return sql_session.scalars(
        select(BookcaseItem).where(BookcaseItem.name == name),
    ).one_or_none()


def search_bookcase_items_by_title(sql_session: Session, text: str) -> list[BookcaseItem]:
    return list(
        sql_session.scalars(
            select(BookcaseItem).where(BookcaseItem.name.ilike(f"%{text}%")),
        ).all(),
    )


def search_bookcase_item_owners(sql_session: Session, text: str) -> list[str]:
    return list(
        sql_session.scalars(
            select(BookcaseItem.owner)
            .where(BookcaseItem.owner.ilike(f"%{text}%"))
            .distinct(),
        ).all(),
    )


def list_bookcase_items_by_owner(sql_session: Session, owner: str) -> list[BookcaseItem]:
    return list(
        sql_session.scalars(
            select(BookcaseItem).where(BookcaseItem.owner == owner),
        ).all(),
    )
