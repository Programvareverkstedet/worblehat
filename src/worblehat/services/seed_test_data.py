import csv
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from worblehat.flaskapp.database import db

from ..models import (
    Author,
    Bookcase,
    BookcaseItem,
    BookcaseItemBorrowing,
    BookcaseItemBorrowingQueue,
    BookcaseShelf,
    Language,
    MediaType,
)


def seed_data(sql_session: Session = db.session):
    media_types = [
        MediaType(name="Book", description="A physical book"),
        MediaType(name="Comic", description="A comic book"),
        MediaType(
            name="Video Game",
            description="A digital game for computers or games consoles",
        ),
        MediaType(
            name="Tabletop Game",
            description="A physical game with cards, boards or similar",
        ),
    ]

    bookcases = [
        Bookcase(name="Unnamed A", description="White case across dibbler"),
        Bookcase(name="Unnamed B", description="Math case in the working room"),
        Bookcase(name="Unnamed C", description="Large case in the working room"),
        Bookcase(name="Unnamed D", description="White comics case in the hallway"),
        Bookcase(name="Unnamed E", description="Wooden comics case in the hallway"),
    ]

    shelfs = [
        BookcaseShelf(row=0, column=0, bookcase=bookcases[0]),
        BookcaseShelf(row=1, column=0, bookcase=bookcases[0]),
        BookcaseShelf(row=2, column=0, bookcase=bookcases[0]),
        BookcaseShelf(row=3, column=0, bookcase=bookcases[0], description="Hacking"),
        BookcaseShelf(row=4, column=0, bookcase=bookcases[0], description="Hacking"),
        BookcaseShelf(row=0, column=1, bookcase=bookcases[0]),
        BookcaseShelf(row=1, column=1, bookcase=bookcases[0]),
        BookcaseShelf(row=2, column=1, bookcase=bookcases[0], description="DOS"),
        BookcaseShelf(
            row=3, column=1, bookcase=bookcases[0], description="Food for thought"
        ),
        BookcaseShelf(row=4, column=1, bookcase=bookcases[0], description="CPP"),
        BookcaseShelf(row=0, column=2, bookcase=bookcases[0]),
        BookcaseShelf(row=1, column=2, bookcase=bookcases[0]),
        BookcaseShelf(row=2, column=2, bookcase=bookcases[0], description="E = mc2"),
        BookcaseShelf(row=3, column=2, bookcase=bookcases[0], description="OBJECTION!"),
        BookcaseShelf(row=4, column=2, bookcase=bookcases[0], description="/home"),
        BookcaseShelf(row=0, column=3, bookcase=bookcases[0]),
        BookcaseShelf(
            row=1, column=3, bookcase=bookcases[0], description="Big indonisian island"
        ),
        BookcaseShelf(row=2, column=3, bookcase=bookcases[0]),
        BookcaseShelf(
            row=3, column=3, bookcase=bookcases[0], description="Div science"
        ),
        BookcaseShelf(row=4, column=3, bookcase=bookcases[0], description="/home"),
        BookcaseShelf(row=0, column=4, bookcase=bookcases[0]),
        BookcaseShelf(row=1, column=4, bookcase=bookcases[0]),
        BookcaseShelf(
            row=2, column=4, bookcase=bookcases[0], description="(not) computer vision"
        ),
        BookcaseShelf(
            row=3, column=4, bookcase=bookcases[0], description="Low voltage"
        ),
        BookcaseShelf(row=4, column=4, bookcase=bookcases[0], description="/home"),
        BookcaseShelf(row=0, column=5, bookcase=bookcases[0]),
        BookcaseShelf(row=1, column=5, bookcase=bookcases[0]),
        BookcaseShelf(row=2, column=5, bookcase=bookcases[0], description="/home"),
        BookcaseShelf(row=3, column=5, bookcase=bookcases[0], description="/home"),
        BookcaseShelf(row=0, column=0, bookcase=bookcases[1]),
        BookcaseShelf(
            row=1,
            column=0,
            bookcase=bookcases[1],
            description="Kjellerarealer og komodovaraner",
        ),
        BookcaseShelf(row=2, column=0, bookcase=bookcases[1]),
        BookcaseShelf(row=3, column=0, bookcase=bookcases[1], description="Quick mafs"),
        BookcaseShelf(row=4, column=0, bookcase=bookcases[1]),
        BookcaseShelf(row=0, column=0, bookcase=bookcases[2]),
        BookcaseShelf(row=1, column=0, bookcase=bookcases[2]),
        BookcaseShelf(row=2, column=0, bookcase=bookcases[2], description="AI"),
        BookcaseShelf(row=3, column=0, bookcase=bookcases[2], description="X86"),
        BookcaseShelf(row=4, column=0, bookcase=bookcases[2], description="Humanoira"),
        BookcaseShelf(
            row=5,
            column=0,
            bookcase=bookcases[2],
            description="Hvem monterte rørforsterker?",
        ),
        BookcaseShelf(row=0, column=1, bookcase=bookcases[2]),
        BookcaseShelf(row=1, column=1, bookcase=bookcases[2], description="Div data"),
        BookcaseShelf(row=2, column=1, bookcase=bookcases[2], description="Chemistry"),
        BookcaseShelf(
            row=3,
            column=1,
            bookcase=bookcases[2],
            description="Soviet Phys. Techn. Phys",
        ),
        BookcaseShelf(
            row=4, column=1, bookcase=bookcases[2], description="Digitalteknikk"
        ),
        BookcaseShelf(row=5, column=1, bookcase=bookcases[2], description="Material"),
        BookcaseShelf(row=0, column=2, bookcase=bookcases[2]),
        BookcaseShelf(
            row=1, column=2, bookcase=bookcases[2], description="Assembler / APL"
        ),
        BookcaseShelf(row=2, column=2, bookcase=bookcases[2], description="Internet"),
        BookcaseShelf(row=3, column=2, bookcase=bookcases[2], description="Algorithms"),
        BookcaseShelf(
            row=4, column=2, bookcase=bookcases[2], description="Soviet Physics Jetp"
        ),
        BookcaseShelf(
            row=5, column=2, bookcase=bookcases[2], description="Død og pine"
        ),
        BookcaseShelf(row=0, column=3, bookcase=bookcases[2]),
        BookcaseShelf(row=1, column=3, bookcase=bookcases[2], description="Web"),
        BookcaseShelf(
            row=2, column=3, bookcase=bookcases[2], description="Div languages"
        ),
        BookcaseShelf(row=3, column=3, bookcase=bookcases[2], description="Python"),
        BookcaseShelf(row=4, column=3, bookcase=bookcases[2], description="D&D Minis"),
        BookcaseShelf(row=5, column=3, bookcase=bookcases[2], description="Perl"),
        BookcaseShelf(row=0, column=4, bookcase=bookcases[2]),
        BookcaseShelf(
            row=1, column=4, bookcase=bookcases[2], description="Knuth on programming"
        ),
        BookcaseShelf(
            row=2, column=4, bookcase=bookcases[2], description="Div languages"
        ),
        BookcaseShelf(
            row=3, column=4, bookcase=bookcases[2], description="Typesetting"
        ),
        BookcaseShelf(row=4, column=4, bookcase=bookcases[2]),
        BookcaseShelf(row=0, column=0, bookcase=bookcases[3]),
        BookcaseShelf(row=0, column=1, bookcase=bookcases[3]),
        BookcaseShelf(row=0, column=2, bookcase=bookcases[3]),
        BookcaseShelf(row=0, column=3, bookcase=bookcases[3]),
        BookcaseShelf(row=0, column=4, bookcase=bookcases[3]),
        BookcaseShelf(row=0, column=0, bookcase=bookcases[4]),
        BookcaseShelf(row=0, column=1, bookcase=bookcases[4]),
        BookcaseShelf(row=0, column=2, bookcase=bookcases[4]),
        BookcaseShelf(row=0, column=3, bookcase=bookcases[4]),
        BookcaseShelf(row=0, column=4, bookcase=bookcases[4], description="Religion"),
    ]

    authors = [
        Author(name="Donald E. Knuth"),
        Author(name="J.K. Rowling"),
        Author(name="J.R.R. Tolkien"),
        Author(name="George R.R. Martin"),
        Author(name="Stephen King"),
        Author(name="Agatha Christie"),
    ]

    book1 = BookcaseItem(
        name="The Art of Computer Programming",
        isbn="9780201896831",
    )
    book1.authors.add(authors[0])
    book1.media_type = media_types[0]
    book1.shelf = shelfs[59]

    book2 = BookcaseItem(
        name="Harry Potter and the Philosopher's Stone",
        isbn="9780747532743",
    )
    book2.authors.add(authors[1])
    book2.media_type = media_types[0]
    book2.shelf = shelfs[-1]

    book_owned_by_other_user = BookcaseItem(
        name="Book owned by other user",
        isbn="9780747532744",
    )

    book_owned_by_other_user.owner = "other_user"
    book_owned_by_other_user.authors.add(authors[4])
    book_owned_by_other_user.media_type = media_types[0]
    book_owned_by_other_user.shelf = shelfs[-2]

    borrowed_book_more_available = BookcaseItem(
        name="Borrowed book with more available",
        isbn="9780747532745",
    )
    borrowed_book_more_available.authors.add(authors[5])
    borrowed_book_more_available.media_type = media_types[0]
    borrowed_book_more_available.shelf = shelfs[-3]
    borrowed_book_more_available.amount = 2

    borrowed_book_no_more_available = BookcaseItem(
        name="Borrowed book with no more available",
        isbn="9780747532746",
    )
    borrowed_book_no_more_available.authors.add(authors[5])
    borrowed_book_no_more_available.media_type = media_types[0]
    borrowed_book_no_more_available.shelf = shelfs[-3]

    borrowed_book_people_in_queue = BookcaseItem(
        name="Borrowed book with people in queue",
        isbn="9780747532747",
    )
    borrowed_book_people_in_queue.authors.add(authors[5])
    borrowed_book_people_in_queue.media_type = media_types[0]
    borrowed_book_people_in_queue.shelf = shelfs[-3]

    borrowed_book_by_slabbedask = BookcaseItem(
        name="Borrowed book by slabbedask",
        isbn="9780747532748",
    )
    borrowed_book_by_slabbedask.authors.add(authors[5])
    borrowed_book_by_slabbedask.media_type = media_types[0]
    borrowed_book_by_slabbedask.shelf = shelfs[-3]

    books = [
        book1,
        book2,
        book_owned_by_other_user,
        borrowed_book_more_available,
        borrowed_book_no_more_available,
        borrowed_book_people_in_queue,
    ]

    slabbedask_borrowing = BookcaseItemBorrowing(
        username="slabbedask",
        item=borrowed_book_more_available,
    )
    slabbedask_borrowing.end_time = datetime.now() - timedelta(days=1)

    borrowings = [
        BookcaseItemBorrowing(username="user", item=borrowed_book_more_available),
        BookcaseItemBorrowing(username="user", item=borrowed_book_no_more_available),
        BookcaseItemBorrowing(username="user", item=borrowed_book_people_in_queue),
        slabbedask_borrowing,
    ]

    queue = [
        BookcaseItemBorrowingQueue(username="user", item=borrowed_book_people_in_queue),
    ]

    with open(Path(__file__).parent.parent.parent / "data" / "iso639_1.csv") as f:
        reader = csv.reader(f)
        languages = [Language(name, code) for (code, name) in reader]

    sql_session.add_all(media_types)
    sql_session.add_all(bookcases)
    sql_session.add_all(shelfs)
    sql_session.add_all(languages)
    sql_session.add_all(authors)
    sql_session.add_all(books)
    sql_session.add_all(borrowings)
    sql_session.add_all(queue)
    sql_session.commit()
    print("Added test media types, bookcases and shelfs.")
