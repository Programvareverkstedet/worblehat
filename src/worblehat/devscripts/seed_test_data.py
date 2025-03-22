import csv

from pathlib import Path

from worblehat.models import (
    Bookcase,
    BookcaseItem,
    BookcaseShelf,
    MediaType,
    Language,
)


CSV_FILE = Path(__file__).parent.parent.parent / "data" / "arbeidsrom_smal_hylle_5.csv"


def clear_db(sql_session):
    sql_session.query(BookcaseItem).delete()
    sql_session.query(BookcaseShelf).delete()
    sql_session.query(Bookcase).delete()
    sql_session.query(MediaType).delete()
    sql_session.query(Language).delete()
    sql_session.commit()


def main(sql_session):
    clear_db(sql_session)

    media_type = MediaType(
        name="Book",
        description="A book",
    )
    sql_session.add(media_type)

    language = Language(
        name="Norwegian",
        iso639_1_code="no",
    )
    sql_session.add(language)

    seed_case = Bookcase(
        name="seed_case",
        description="test bookcase with test data",
    )
    sql_session.add(seed_case)

    seed_shelf_1 = BookcaseShelf(
        row=1,
        column=1,
        bookcase=seed_case,
        description="test shelf with test data 1",
    )
    seed_shelf_2 = BookcaseShelf(
        row=2,
        column=1,
        bookcase=seed_case,
        description="test shelf with test data 2",
    )
    sql_session.add(seed_shelf_1)
    sql_session.add(seed_shelf_2)

    bookcase_items = []
    with open(CSV_FILE) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")

        next(csv_reader)
        for row in csv_reader:
            item = BookcaseItem(
                isbn=row[0],
                name=row[1],
            )
            item.media_type = media_type
            item.language = language
            bookcase_items.append(item)

    half = len(bookcase_items) // 2
    first_half = bookcase_items[:half]
    second_half = bookcase_items[half:]

    for item in first_half:
        seed_shelf_1.items.add(item)

    for item in second_half:
        seed_shelf_2.items.add(item)

    sql_session.add_all(bookcase_items)
    sql_session.commit()
