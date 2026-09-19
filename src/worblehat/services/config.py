import tomllib
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from pprint import pformat
from typing import Any


class _Default(Enum):
    REQUIRED = auto()


_REQUIRED = _Default.REQUIRED


@dataclass(frozen=True)
class ConfigField:
    type: type
    default: Any = _REQUIRED


GENERAL_SCHEMA: dict[str, ConfigField] = {
    "crashdump_dir": ConfigField(str),
    "quit_allowed": ConfigField(bool),
}

LOGGING_SCHEMA: dict[str, ConfigField] = {
    "debug": ConfigField(bool),
    "debug_sql": ConfigField(bool),
}

DATABASE_SQLITE_SCHEMA: dict[str, ConfigField] = {
    "path": ConfigField(str),
}

DATABASE_POSTGRESQL_SCHEMA: dict[str, ConfigField] = {
    "host": ConfigField(str),
    "port": ConfigField(int),
    "username": ConfigField(str),
    "password": ConfigField(str),
    "database": ConfigField(str),
}

SMTP_SCHEMA: dict[str, ConfigField] = {
    "enabled": ConfigField(bool),
    "host": ConfigField(str),
    "port": ConfigField(int),
    "username": ConfigField(str),
    "password": ConfigField(str),
    "from": ConfigField(str),
    "subject_prefix": ConfigField(str),
}

DEADLINE_DAEMON_SCHEMA: dict[str, ConfigField] = {
    "enabled": ConfigField(bool),
    "dryrun": ConfigField(bool),
    "warn_days_before_borrowing_deadline": ConfigField(list),
    "days_before_queue_position_expires": ConfigField(int),
    "warn_days_before_expiring_queue_position_deadline": ConfigField(list),
}


class Config:
    """
    This class is a singleton which holds the configuration for the
    application. It is initialized by calling `Config.load_configuration()`
    with a dictionary of arguments. The arguments are usually the result
    of calling `vars(arg_parser.parse_args())` where `arg_parser` is the
    argument parser from `worblehat/services/argument_parser.py`.

    The class also provides some utility functions for accessing several
    kinds of values that depend on the configuration.
    """

    _config = None
    _expected_config_file_locations = [
        Path("./config.toml"),
        Path("~/.config/worblehat/config.toml"),
        Path("/etc/worblehat/config.toml"),
    ]

    def __class_getitem__(cls, name: str) -> Any:
        if cls._config is None:
            raise RuntimeError(
                "Configuration not loaded, call Config.load_configuration() first.",
            )

        __config = cls._config
        for attr in name.split("."):
            __config = __config.get(attr)
            if __config is None:
                raise AttributeError(f"No such attribute: {name}")
        return __config

    @staticmethod
    def read_password(password_field: str) -> str:
        if Path(password_field).is_file():
            with Path(password_field).open() as f:
                return f.read().strip()
        else:
            return password_field

    @classmethod
    def _locate_configuration_file(cls) -> Path | None:
        for path in cls._expected_config_file_locations:
            if path.is_file():
                return path
        return None

    @classmethod
    def _load_configuration_from_file(
        cls,
        config_file_path: str | None,
    ) -> dict[str, Any]:
        if config_file_path is None:
            config_file_path = cls._locate_configuration_file()

        if config_file_path is None:
            print("Error: could not locate configuration file.")
            exit(1)

        with config_file_path.open("rb") as config_file:
            return tomllib.load(config_file)

    @classmethod
    def db_string(cls) -> str:
        db_type = cls._config.get("database").get("type")

        if db_type == "sqlite":
            path = Path(cls._config.get("database").get("sqlite").get("path"))
            return f"sqlite:///{path.absolute()}"

        if db_type == "postgresql":
            db_config = cls._config.get("database").get("postgresql")
            host = db_config.get("host")
            port = db_config.get("port")
            username = db_config.get("username")
            password = cls.read_password(db_config.get("password"))
            database = db_config.get("database")
            if host.startswith("/"):
                return f"postgresql+psycopg2://{username}:{password}@/{database}?host={host}"
            return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        print(f"Error: unknown database type '{db_config.get('type')}'")
        exit(1)

    @classmethod
    def db_string_no_password(cls) -> str:
        db_type = cls._config.get("database").get("type")

        if db_type == "sqlite":
            path = Path(cls._config.get("database").get("sqlite").get("path"))
            return f"sqlite:///{path.absolute()}"

        if db_type == "postgresql":
            db_config = cls._config.get("database").get("postgresql")
            host = db_config.get("host")
            port = db_config.get("port")
            username = db_config.get("username")
            database = db_config.get("database")
            if host.startswith("/"):
                return f"postgresql+psycopg2://{username}:<password>@/{database}?host={host}"
            return f"postgresql+psycopg2://{username}:<password>@{host}:{port}/{database}"
        print(f"Error: unknown database type '{db_config.get('type')}'")
        exit(1)

    @classmethod
    def debug(cls) -> str:
        return pformat(cls._config)

    @staticmethod
    def _validate_section(
        data: Any,
        schema: dict[str, ConfigField] | None,
        path: str,
        errors: list[str],
    ) -> dict[str, Any] | None:
        if not isinstance(data, dict):
            errors.append(f"Missing or invalid [{path}] section")
            return None
        if schema is None:
            return data
        for key, field in schema.items():
            if key not in data:
                errors.append(f"Missing required config key: {path}.{key}")
                continue
            if not isinstance(data[key], field.type):
                errors.append(f"Config key {path}.{key} must be of type {field.type.__name__}")
        return data

    @classmethod
    def validate_configuration(cls) -> list[str]:
        errors: list[str] = []
        config = cls._config

        cls._validate_section(config.get("general"), GENERAL_SCHEMA, "general", errors)
        cls._validate_section(config.get("logging"), LOGGING_SCHEMA, "logging", errors)
        cls._validate_section(config.get("smtp"), SMTP_SCHEMA, "smtp", errors)
        cls._validate_section(
            config.get("deadline_daemon"),
            DEADLINE_DAEMON_SCHEMA,
            "deadline_daemon",
            errors,
        )
        cls._validate_section(config.get("flask"), None, "flask", errors)

        database = cls._validate_section(config.get("database"), None, "database", errors)
        if database is not None:
            db_type = database.get("type")
            if db_type not in ("sqlite", "postgresql"):
                errors.append(
                    f"Config key database.type must be 'sqlite' or 'postgresql', got {db_type!r}",
                )
            elif db_type == "sqlite":
                cls._validate_section(
                    database.get("sqlite"),
                    DATABASE_SQLITE_SCHEMA,
                    "database.sqlite",
                    errors,
                )
            elif db_type == "postgresql":
                cls._validate_section(
                    database.get("postgresql"),
                    DATABASE_POSTGRESQL_SCHEMA,
                    "database.postgresql",
                    errors,
                )

        return errors

    @classmethod
    def load_configuration(cls, args: dict[str, Any]) -> dict[str, any]:
        cls._config = cls._load_configuration_from_file(args.get("config_file"))

        errors = cls.validate_configuration()
        if errors:
            print("Error: invalid configuration:")
            for error in errors:
                print(f"  - {error}")
            exit(1)
