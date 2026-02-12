from .flaskapp import create_app


def main() -> None:
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()
