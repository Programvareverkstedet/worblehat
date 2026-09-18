from typing import ClassVar, NamedTuple

from sqlalchemy import DDL, event

from ..Base import Base


class Trigger(NamedTuple):
    """
    A `CREATE TRIGGER` statement to run for a `Projection` subclass.

    Be careful to ensure that the `name` and `table` matches the create statement.
    """

    name: str
    table: str
    create: str


class Function(NamedTuple):
    """
    A `CREATE FUNCTION` statement that a PostgreSQL trigger depends on.

    Be careful to ensure that the `name` matches the create statement.
    """

    name: str
    create: str


class DialectTriggers(NamedTuple):
    triggers: tuple[Trigger, ...]
    functions: tuple[Function, ...] = ()


class Projection(Base):
    """
    A base class for tables that are trigger-based projections of other tables.
    They are disposable renderings of the underlying data, can be thought of as
    materialized views, and are only meant to be generated via provided triggers.
    """

    __abstract__ = True

    sqlite_triggers: ClassVar[DialectTriggers | None] = None
    postgresql_triggers: ClassVar[DialectTriggers | None] = None

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)

        if (cls.sqlite_triggers is None) != (cls.postgresql_triggers is None):
            raise TypeError(
                f"{cls.__name__} must define both sqlite_triggers and postgresql_triggers",
            )
        if cls.sqlite_triggers is None or cls.postgresql_triggers is None:
            return

        for dialect, dialect_triggers in (
            ("sqlite", cls.sqlite_triggers),
            ("postgresql", cls.postgresql_triggers),
        ):
            for function in dialect_triggers.functions:
                event.listen(
                    cls.metadata,
                    "after_create",
                    DDL(function.create).execute_if(dialect=dialect),
                )

            for trigger in dialect_triggers.triggers:
                event.listen(
                    cls.metadata,
                    "after_create",
                    DDL(trigger.create).execute_if(dialect=dialect),
                )

            for trigger in reversed(dialect_triggers.triggers):
                drop = (
                    f"DROP TRIGGER IF EXISTS {trigger.name}"
                    if dialect == "sqlite"
                    else f'DROP TRIGGER IF EXISTS {trigger.name} ON "{trigger.table}"'
                )
                event.listen(cls.metadata, "before_drop", DDL(drop).execute_if(dialect=dialect))

            for function in reversed(dialect_triggers.functions):
                event.listen(
                    cls.metadata,
                    "before_drop",
                    DDL(f"DROP FUNCTION IF EXISTS {function.name}()").execute_if(dialect=dialect),
                )
