from __future__ import annotations

from datetime import datetime
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

from .Projection import DialectTriggers, Function, Projection, Trigger

if TYPE_CHECKING:
    from ..BookcaseItem import BookcaseItem


class Borrowing(Projection):
    """All active borrowings, excluding those that have been returned."""

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("bookcase_item.uid"),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    due_time: Mapped[datetime] = mapped_column(DateTime)

    item: Mapped[BookcaseItem] = relationship(back_populates="borrowings")

    def __init__(self, username: str, item: BookcaseItem, due_time: datetime) -> None:
        self.username = username
        self.item = item
        self.due_time = due_time

    sqlite_triggers = DialectTriggers(
        triggers=(
            Trigger(
                name="trg_borrowinglog_borrowed",
                table="borrowing_log",
                create="""
                    CREATE TRIGGER trg_borrowinglog_borrowed
                    AFTER INSERT ON "borrowing_log"
                    WHEN NEW.event_type = 'borrowed'
                    BEGIN
                        INSERT INTO "borrowing" (fk_bookcase_item_uid, username, due_time)
                        VALUES (NEW.fk_bookcase_item_uid, NEW.username, NEW.due_time);
                    END
                """,
            ),
            Trigger(
                name="trg_borrowinglog_renewed",
                table="borrowing_log",
                create="""
                    CREATE TRIGGER trg_borrowinglog_renewed
                    AFTER INSERT ON "borrowing_log"
                    WHEN NEW.event_type = 'renewed'
                    BEGIN
                        UPDATE "borrowing"
                        SET due_time = NEW.due_time
                        WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                          AND username = NEW.username;
                    END
                """,
            ),
            Trigger(
                name="trg_borrowinglog_returned",
                table="borrowing_log",
                create="""
                    CREATE TRIGGER trg_borrowinglog_returned
                    AFTER INSERT ON "borrowing_log"
                    WHEN NEW.event_type = 'returned'
                    BEGIN
                        DELETE FROM "borrowing"
                        WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                          AND username = NEW.username;
                    END
                """,
            ),
        ),
    )
    postgresql_triggers = DialectTriggers(
        functions=(
            Function(
                name="fn_sync_borrowing_projection",
                create="""
                    CREATE FUNCTION fn_sync_borrowing_projection() RETURNS TRIGGER AS $$
                    BEGIN
                        IF NEW.event_type = 'borrowed' THEN
                            INSERT INTO "borrowing" (fk_bookcase_item_uid, username, due_time)
                            VALUES (NEW.fk_bookcase_item_uid, NEW.username, NEW.due_time);
                        ELSIF NEW.event_type = 'renewed' THEN
                            UPDATE "borrowing"
                            SET due_time = NEW.due_time
                            WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                              AND username = NEW.username;
                        ELSIF NEW.event_type = 'returned' THEN
                            DELETE FROM "borrowing"
                            WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                              AND username = NEW.username;
                        END IF;
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql
                """,
            ),
        ),
        triggers=(
            Trigger(
                name="trg_borrowinglog_sync_borrowing",
                table="borrowing_log",
                create="""
                    CREATE TRIGGER trg_borrowinglog_sync_borrowing
                    AFTER INSERT ON "borrowing_log"
                    FOR EACH ROW
                    EXECUTE FUNCTION fn_sync_borrowing_projection()
                """,
            ),
        ),
    )
