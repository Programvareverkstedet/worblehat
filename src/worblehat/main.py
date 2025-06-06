import logging
from pprint import pformat

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .services import (
    Config,
    arg_parser,
    devscripts_arg_parser,
)

from .deadline_daemon import DeadlineDaemon
from .cli import WorblehatCli
from .flaskapp.wsgi_dev import main as flask_dev_main
from .flaskapp.wsgi_prod import main as flask_prod_main


def _print_version() -> None:
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("worblehat")
    except PackageNotFoundError:
        __version__ = "unknown"

    print(f"Worblehat version {__version__}")


def _connect_to_database(**engine_args) -> Session:
    try:
        engine = create_engine(Config.db_string(), **engine_args)
        sql_session = Session(engine)
    except Exception as err:
        print("Error: could not connect to database.")
        print(err)
        exit(1)

    print(f"Debug: Connected to database at '{Config.db_string()}'")
    return sql_session


def main():
    args = arg_parser.parse_args()
    Config.load_configuration(vars(args))

    if Config["logging.debug"]:
        logging.basicConfig(encoding="utf-8", level=logging.DEBUG)
    else:
        logging.basicConfig(encoding="utf-8", level=logging.INFO)

    if args.version:
        _print_version()
        exit(0)

    if args.print_config:
        print(f"Configuration:\n{pformat(vars(args))}")
        exit(0)

    if args.command == "deadline-daemon":
        sql_session = _connect_to_database(echo=Config["logging.debug_sql"])
        DeadlineDaemon(sql_session).run()
        exit(0)

    if args.command == "cli":
        sql_session = _connect_to_database(echo=Config["logging.debug_sql"])
        WorblehatCli.run_with_safe_exit_wrapper(sql_session)
        exit(0)

    if args.command == "devscripts":
        sql_session = _connect_to_database(echo=Config["logging.debug_sql"])
        if args.script == "seed-content-for-deadline-daemon":
            from .devscripts.seed_content_for_deadline_daemon import main

            main(sql_session)
        elif args.script == "seed-test-data":
            from .devscripts.seed_test_data import main

            main(sql_session)
        else:
            print(devscripts_arg_parser.format_help())
            exit(1)
        exit(0)

    if args.command == "flask-dev":
        flask_dev_main()
        exit(0)

    if args.command == "flask-prod":
        if Config["logging.debug"] or Config["logging.debug_sql"]:
            logging.warn(
                "Debug mode is enabled for the production server. This is not recommended."
            )
        flask_prod_main()
        exit(0)

    print(arg_parser.format_help())
    exit(1)
