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


class QueuePosition(Projection):
    """
    All active queue positions, including awaiting and grace period ones.
    """

    fk_bookcase_item_uid: Mapped[int] = mapped_column(
        ForeignKey("BookcaseItem.uid"),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(String, primary_key=True, index=True)

    entered_queue_time: Mapped[datetime] = mapped_column(DateTime)

    item: Mapped[BookcaseItem] = relationship(back_populates="queue_positions")

    # Set once the item becomes available for this position, during the
    # grace period before the position either gets claimed or expires.
    notified_available_time: Mapped[datetime | None] = mapped_column(
        DateTime,
        default=None,
    )

    def __init__(
        self,
        username: str,
        item: BookcaseItem,
        entered_queue_time: datetime | None = None,
    ) -> None:
        self.username = username
        self.item = item
        self.entered_queue_time = (
            entered_queue_time if entered_queue_time is not None else datetime.now()
        )

    sqlite_triggers = DialectTriggers(
        triggers=(
            Trigger(
                name="trg_queuelog_joined",
                table="QueueLog",
                create="""
                    CREATE TRIGGER trg_queuelog_joined
                    AFTER INSERT ON "QueueLog"
                    WHEN NEW.event_type = 'joined'
                    BEGIN
                        INSERT INTO "QueuePosition" (fk_bookcase_item_uid, username, entered_queue_time)
                        VALUES (NEW.fk_bookcase_item_uid, NEW.username, NEW.timestamp);
                    END
                """,
            ),
            Trigger(
                name="trg_queuelog_notified",
                table="QueueLog",
                create="""
                    CREATE TRIGGER trg_queuelog_notified
                    AFTER INSERT ON "QueueLog"
                    WHEN NEW.event_type = 'notified'
                    BEGIN
                        UPDATE "QueuePosition"
                        SET notified_available_time = NEW.timestamp
                        WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                          AND username = NEW.username;
                    END
                """,
            ),
            Trigger(
                name="trg_queuelog_left_expired_claimed",
                table="QueueLog",
                create="""
                    CREATE TRIGGER trg_queuelog_left_expired_claimed
                    AFTER INSERT ON "QueueLog"
                    WHEN NEW.event_type IN ('left', 'expired', 'claimed')
                    BEGIN
                        DELETE FROM "QueuePosition"
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
                name="fn_sync_queueposition_projection",
                create="""
                    CREATE FUNCTION fn_sync_queueposition_projection() RETURNS TRIGGER AS $$
                    BEGIN
                        IF NEW.event_type = 'joined' THEN
                            INSERT INTO "QueuePosition" (fk_bookcase_item_uid, username, entered_queue_time)
                            VALUES (NEW.fk_bookcase_item_uid, NEW.username, NEW.timestamp);
                        ELSIF NEW.event_type = 'notified' THEN
                            UPDATE "QueuePosition"
                            SET notified_available_time = NEW.timestamp
                            WHERE fk_bookcase_item_uid = NEW.fk_bookcase_item_uid
                              AND username = NEW.username;
                        ELSIF NEW.event_type IN ('left', 'expired', 'claimed') THEN
                            DELETE FROM "QueuePosition"
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
                name="trg_queuelog_sync_queueposition",
                table="QueueLog",
                create="""
                    CREATE TRIGGER trg_queuelog_sync_queueposition
                    AFTER INSERT ON "QueueLog"
                    FOR EACH ROW
                    EXECUTE FUNCTION fn_sync_queueposition_projection()
                """,
            ),
        ),
    )
