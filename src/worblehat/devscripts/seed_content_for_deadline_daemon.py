from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from worblehat.models import (
    BookcaseItem,
    Borrowing,
    BorrowingEventType,
    BorrowingLog,
    DeadlineDaemonLastRunDatetime,
    QueueEventType,
    QueueLog,
    QueuePosition,
)
from worblehat.services.config import Config

from .seed_test_data import main as seed_test_data_main


def clear_db(sql_session: Session) -> None:
    sql_session.query(QueueLog).delete()
    sql_session.query(BorrowingLog).delete()
    sql_session.query(QueuePosition).delete()
    sql_session.query(Borrowing).delete()
    sql_session.query(DeadlineDaemonLastRunDatetime).delete()
    sql_session.commit()


# NOTE: feel free to change this function to suit your needs
#       it's just a quick and dirty way to get some data into the database
#       for testing the deadline daemon - oysteikt 2024
def main(sql_session: Session) -> None:
    borrow_warning_days = [
        timedelta(days=int(d))
        for d in Config["deadline_daemon.warn_days_before_borrowing_deadline"]
    ]
    queue_warning_days = [
        timedelta(days=int(d))
        for d in Config["deadline_daemon.warn_days_before_expiring_queue_position_deadline"]
    ]
    queue_expire_days = int(
        Config["deadline_daemon.days_before_queue_position_expires"],
    )

    clear_db(sql_session)
    seed_test_data_main(sql_session)

    books = sql_session.query(BookcaseItem).all()

    last_run_datetime = datetime.now() - timedelta(days=16)
    last_run = DeadlineDaemonLastRunDatetime(last_run_datetime)
    sql_session.add(last_run)

    # Create at least one item that is borrowed and not supposed to be returned yet
    sql_session.add(
        BorrowingLog(
            "test_borrower_still_borrowing",
            books[0],
            BorrowingEventType.BORROWED,
            due_time=datetime.now() - timedelta(days=6),
            timestamp=last_run_datetime - timedelta(days=1),
        ),
    )

    # Create at least one item that is borrowed and is supposed to be returned soon
    sql_session.add(
        BorrowingLog(
            "test_borrower_return_soon",
            books[1],
            BorrowingEventType.BORROWED,
            due_time=datetime.now() - timedelta(days=2),
            timestamp=last_run_datetime - timedelta(days=1),
        ),
    )

    # Create at least one item that is borrowed and is overdue
    sql_session.add(
        BorrowingLog(
            "test_borrower_overdue",
            books[2],
            BorrowingEventType.BORROWED,
            due_time=datetime.now() + timedelta(days=1),
            timestamp=datetime.now() - timedelta(days=1),
        ),
    )

    # Create at least one item that is in the queue and is not supposed to be borrowed yet
    sql_session.add(
        QueueLog(
            "test_queue_user_still_waiting",
            books[3],
            QueueEventType.JOINED,
            timestamp=last_run_datetime - timedelta(days=1),
        ),
    )
    sql_session.add(
        BorrowingLog(
            "test_borrower_return_soon",
            books[3],
            BorrowingEventType.BORROWED,
            due_time=datetime.now() - timedelta(days=2),
            timestamp=last_run_datetime - timedelta(days=1),
        ),
    )

    # Create at least three items that is in the queue and two items were just returned
    for i in range(3):
        sql_session.add(
            QueueLog(f"test_queue_user_{i}", books[4 + i], QueueEventType.JOINED),
        )

    for i in range(3):
        username = f"test_borrower_returned_{i}"
        item = books[4 + i]
        sql_session.add(
            BorrowingLog(
                username,
                item,
                BorrowingEventType.BORROWED,
                due_time=datetime.now() + timedelta(days=1),
                timestamp=last_run_datetime - timedelta(days=2),
            ),
        )

        if i != 2:
            sql_session.add(
                BorrowingLog(
                    username,
                    item,
                    BorrowingEventType.RETURNED,
                    timestamp=datetime.now() - timedelta(days=1),
                ),
            )

    # Create at least one item that has been in the queue for so long that the queue position should expire
    sql_session.add(
        QueueLog(
            "test_queue_user_expired",
            books[7],
            QueueEventType.JOINED,
            timestamp=datetime.now() - timedelta(days=15),
        ),
    )

    # Create at least one item that has been in the queue for so long that the queue position should expire,
    # but the queue person has already been notified
    sql_session.add(
        QueueLog(
            "test_queue_user_expired_notified",
            books[8],
            QueueEventType.JOINED,
            timestamp=datetime.now() - timedelta(days=15),
        ),
    )
    sql_session.add(
        QueueLog(
            "test_queue_user_expired_notified",
            books[8],
            QueueEventType.NOTIFIED,
            timestamp=datetime.now() - timedelta(days=queue_expire_days + 1),
        ),
    )

    sql_session.commit()
