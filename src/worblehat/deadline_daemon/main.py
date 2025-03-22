import logging
from datetime import datetime, timedelta
from textwrap import dedent

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from worblehat.services.config import Config
from worblehat.models import (
    BookcaseItemBorrowing,
    DeadlineDaemonLastRunDatetime,
    BookcaseItemBorrowingQueue,
)

from worblehat.services.email import send_email


class DeadlineDaemon:
    def __init__(self, sql_session: Session):
        if not Config["deadline_daemon.enabled"]:
            return

        self.sql_session = sql_session

        self.last_run = self.sql_session.scalars(
            select(DeadlineDaemonLastRunDatetime),
        ).one_or_none()

        if self.last_run is None:
            logging.info("No previous run found, assuming this is the first run")
            self.last_run = DeadlineDaemonLastRunDatetime(time=datetime.now())
            self.sql_session.add(self.last_run)
            self.sql_session.commit()

        self.last_run_datetime = self.last_run.time
        self.current_run_datetime = datetime.now()

    def run(self):
        logging.info("Deadline daemon started")
        if not Config["deadline_daemon.enabled"]:
            logging.warn("Deadline daemon disabled, exiting")
            return

        if Config["deadline_daemon.dryrun"]:
            logging.warn("Running in dryrun mode")

        self.send_close_deadline_reminder_mails()
        self.send_overdue_mails()
        self.send_newly_available_mails()
        self.send_expiring_queue_position_mails()
        self.auto_expire_queue_positions()

        self.last_run.time = self.current_run_datetime
        self.sql_session.commit()

    ###################
    # EMAIL TEMPLATES #
    ###################

    def _send_close_deadline_mail(self, borrowing: BookcaseItemBorrowing):
        logging.info(
            f"Sending close deadline mail to {borrowing.username}@pvv.ntnu.no."
        )
        send_email(
            f"{borrowing.username}@pvv.ntnu.no",
            "Reminder - Your borrowing deadline is approaching",
            dedent(
                f"""
                Your borrowing deadline for the following item is approaching:
                
                {borrowing.item.name}
                
                Please return the item by {borrowing.end_time.strftime("%a %b %d, %Y")}
                """,
            ).strip(),
        )

    def _send_overdue_mail(self, borrowing: BookcaseItemBorrowing):
        logging.info(
            f"Sending overdue mail to {borrowing.username}@pvv.ntnu.no for {borrowing.item.isbn} - {borrowing.end_time.strftime('%a %b %d, %Y')}"
        )
        send_email(
            f"{borrowing.username}@pvv.ntnu.no",
            "Your deadline has passed",
            dedent(
                f"""
                Your delivery deadline for the following item has passed:
                
                {borrowing.item.name}
                
                Please return the item as soon as possible.
                """,
            ).strip(),
        )

    def _send_newly_available_mail(self, queue_item: BookcaseItemBorrowingQueue):
        logging.info(f"Sending newly available mail to {queue_item.username}")

        days_before_queue_expires = Config[
            "deadline_daemon.days_before_queue_position_expires"
        ]

        # TODO: calculate and format the date of when the queue position expires in the mail.
        send_email(
            f"{queue_item.username}@pvv.ntnu.no",
            "An item you have queued for is now available",
            dedent(
                f"""
                The following item is now available for you to borrow:

                {queue_item.item.name}

                Please pick up the item within {days_before_queue_expires} days.
                """,
            ).strip(),
        )

    def _send_expiring_queue_position_mail(
        self, queue_position: BookcaseItemBorrowingQueue, day: int
    ):
        logging.info(
            f"Sending queue position expiry reminder to {queue_position.username}@pvv.ntnu.no."
        )
        send_email(
            f"{queue_position.username}@pvv.ntnu.no",
            "Reminder - Your queue position expiry deadline is approaching",
            dedent(
                f"""
                Your queue position expiry deadline for the following item is approaching:
                
                {queue_position.item.name}
                
                Please borrow the item by {(queue_position.item_became_available_time + timedelta(days=day)).strftime("%a %b %d, %Y")}
                """,
            ).strip(),
        )

    def _send_queue_position_expired_mail(
        self, queue_position: BookcaseItemBorrowingQueue
    ):
        send_email(
            f"{queue_position.username}@pvv.ntnu.no",
            "Your queue position has expired",
            dedent(
                f"""
                Your queue position for the following item has expired:
                
                {queue_position.item.name}
                
                You can queue for the item again at any time, but you will be placed at the back of the queue.

                There are currently {len(queue_position.item.borrowing_queue)} users in the queue.
                """,
            ).strip(),
        )

    ##################
    # EMAIL ROUTINES #
    ##################

    def _sql_subtract_date(self, x: datetime, y: timedelta):
        if self.sql_session.bind.dialect.name == "sqlite":
            # SQLite does not support timedelta in queries
            return func.datetime(x, f"-{y.days} days")
        elif self.sql_session.bind.dialect.name == "postgresql":
            return x - y
        else:
            raise NotImplementedError(
                f"Unsupported dialect: {self.sql_session.bind.dialect.name}"
            )

    def send_close_deadline_reminder_mails(self):
        logging.info("Sending mails for items with a closing deadline")

        # TODO: This should be int-parsed and validated before the daemon started
        days = [
            int(d)
            for d in Config["deadline_daemon.warn_days_before_borrowing_deadline"]
        ]

        for day in days:
            borrowings_to_remind = self.sql_session.scalars(
                select(BookcaseItemBorrowing).where(
                    self._sql_subtract_date(
                        BookcaseItemBorrowing.end_time,
                        timedelta(days=day),
                    ).between(
                        self.last_run_datetime,
                        self.current_run_datetime,
                    ),
                    BookcaseItemBorrowing.delivered.is_(None),
                ),
            ).all()
            for borrowing in borrowings_to_remind:
                self._send_close_deadline_mail(borrowing)

    def send_overdue_mails(self):
        logging.info("Sending mails for overdue items")

        to_remind = self.sql_session.scalars(
            select(BookcaseItemBorrowing).where(
                BookcaseItemBorrowing.end_time < self.current_run_datetime,
                BookcaseItemBorrowing.delivered.is_(None),
            )
        ).all()

        for borrowing in to_remind:
            self._send_overdue_mail(borrowing)

    def send_newly_available_mails(self):
        logging.info("Sending mails about newly available items")

        newly_available = self.sql_session.scalars(
            select(BookcaseItemBorrowingQueue)
            .join(
                BookcaseItemBorrowing,
                BookcaseItemBorrowing.fk_bookcase_item_uid
                == BookcaseItemBorrowingQueue.fk_bookcase_item_uid,
            )
            .where(
                BookcaseItemBorrowingQueue.expired.is_(False),
                BookcaseItemBorrowing.delivered.is_not(None),
                BookcaseItemBorrowing.delivered.between(
                    self.last_run_datetime,
                    self.current_run_datetime,
                ),
            )
            .order_by(BookcaseItemBorrowingQueue.entered_queue_time)
            .group_by(BookcaseItemBorrowingQueue.fk_bookcase_item_uid)
        ).all()

        for queue_item in newly_available:
            logging.info(
                f"Adding user {queue_item.username} to queue for {queue_item.item.name}"
            )
            queue_item.item_became_available_time = self.current_run_datetime
            self.sql_session.commit()

            self._send_newly_available_mail(queue_item)

    def send_expiring_queue_position_mails(self):
        logging.info("Sending mails about queue positions which are expiring soon")
        logging.warning("Not implemented")

        days = [
            int(d)
            for d in Config[
                "deadline_daemon.warn_days_before_expiring_queue_position_deadline"
            ]
        ]
        for day in days:
            queue_positions_to_remind = self.sql_session.scalars(
                select(BookcaseItemBorrowingQueue)
                .join(
                    BookcaseItemBorrowing,
                    BookcaseItemBorrowing.fk_bookcase_item_uid
                    == BookcaseItemBorrowingQueue.fk_bookcase_item_uid,
                )
                .where(
                    self._sql_subtract_date(
                        BookcaseItemBorrowingQueue.item_became_available_time
                        + timedelta(days=day),
                        timedelta(days=day),
                    ).between(
                        self.last_run_datetime,
                        self.current_run_datetime,
                    ),
                ),
            ).all()

            for queue_position in queue_positions_to_remind:
                self._send_expiring_queue_position_mail(queue_position, day)

    def auto_expire_queue_positions(self):
        logging.info("Expiring queue positions which are too old")

        queue_position_expiry_days = int(
            Config["deadline_daemon.days_before_queue_position_expires"]
        )

        overdue_queue_positions = self.sql_session.scalars(
            select(BookcaseItemBorrowingQueue).where(
                BookcaseItemBorrowingQueue.item_became_available_time
                + timedelta(days=queue_position_expiry_days)
                < self.current_run_datetime,
                BookcaseItemBorrowingQueue.expired.is_(False),
            ),
        ).all()

        for queue_position in overdue_queue_positions:
            logging.info(
                f"Expiring queue position for {queue_position.username} for item {queue_position.item.name}"
            )

            queue_position.expired = True

            next_queue_position = self.sql_session.scalars(
                select(BookcaseItemBorrowingQueue)
                .where(
                    BookcaseItemBorrowingQueue.fk_bookcase_item_uid
                    == queue_position.fk_bookcase_item_uid,
                    BookcaseItemBorrowingQueue.item_became_available_time.is_(None),
                )
                .order_by(BookcaseItemBorrowingQueue.entered_queue_time)
                .limit(1),
            ).one_or_none()

            self._send_queue_position_expired_mail(queue_position)

            if next_queue_position is not None:
                next_queue_position.item_became_available_time = (
                    self.current_run_datetime
                )

                logging.info(
                    f"Next user in queue for item {next_queue_position.item.name} is {next_queue_position.username}"
                )
                self._send_newly_available_mail(next_queue_position)

            self.sql_session.commit()
