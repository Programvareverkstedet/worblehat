from datetime import datetime, timedelta

from worblehat.models import (
  BookcaseItem,
  BookcaseItemBorrowing,
  BookcaseItemBorrowingQueue,
  DeadlineDaemonLastRunDatetime,
)

from worblehat.services.config import Config

from .seed_test_data import main as seed_test_data_main


def clear_db(sql_session):
  sql_session.query(BookcaseItemBorrowingQueue).delete()
  sql_session.query(BookcaseItemBorrowing).delete()
  sql_session.query(DeadlineDaemonLastRunDatetime).delete()
  sql_session.commit()

# NOTE: feel free to change this function to suit your needs
#       it's just a quick and dirty way to get some data into the database
#       for testing the deadline daemon - oysteikt 2024
def main(sql_session):
  borrow_warning_days = [timedelta(days=int(d)) for d in Config['deadline_daemon.warn_days_before_borrowing_deadline']]
  queue_warning_days = [timedelta(days=int(d)) for d in Config['deadline_daemon.warn_days_before_expiring_queue_position_deadline']]
  queue_expire_days = int(Config['deadline_daemon.days_before_queue_position_expires'])

  clear_db(sql_session)
  seed_test_data_main(sql_session)

  books = sql_session.query(BookcaseItem).all()

  last_run_datetime = datetime.now() - timedelta(days=16)
  last_run = DeadlineDaemonLastRunDatetime(last_run_datetime)
  sql_session.add(last_run)

  # Create at least one item that is borrowed and not supposed to be returned yet
  borrowing = BookcaseItemBorrowing(
    item=books[0],
    username='test_borrower_still_borrowing',
  )
  borrowing.start_time = last_run_datetime - timedelta(days=1)
  borrowing.end_time = datetime.now() - timedelta(days=6)
  sql_session.add(borrowing)

  # Create at least one item that is borrowed and is supposed to be returned soon
  borrowing = BookcaseItemBorrowing(
    item=books[1],
    username='test_borrower_return_soon',
  )
  borrowing.start_time = last_run_datetime - timedelta(days=1)
  borrowing.end_time = datetime.now() - timedelta(days=2)
  sql_session.add(borrowing)

  # Create at least one item that is borrowed and is overdue
  borrowing = BookcaseItemBorrowing(
    item=books[2],
    username='test_borrower_overdue',
  )
  borrowing.start_time = datetime.now() - timedelta(days=1)
  borrowing.end_time = datetime.now() + timedelta(days=1)
  sql_session.add(borrowing)

  # Create at least one item that is in the queue and is not supposed to be borrowed yet
  queue_item = BookcaseItemBorrowingQueue(
    item=books[3],
    username='test_queue_user_still_waiting',
  )
  queue_item.entered_queue_time = last_run_datetime - timedelta(days=1)
  borrowing = BookcaseItemBorrowing(
    item=books[3],
    username='test_borrower_return_soon',
  )
  borrowing.start_time = last_run_datetime - timedelta(days=1)
  borrowing.end_time = datetime.now() - timedelta(days=2)
  sql_session.add(queue_item)
  sql_session.add(borrowing)

  # Create at least three items that is in the queue and two items were just returned
  for i in range(3):
    queue_item = BookcaseItemBorrowingQueue(
      item=books[4 + i],
      username=f'test_queue_user_{i}',
    )
    sql_session.add(queue_item)

  for i in range(3):
    borrowing = BookcaseItemBorrowing(
      item=books[4 + i],
      username=f'test_borrower_returned_{i}',
    )
    borrowing.start_time = last_run_datetime - timedelta(days=2)
    borrowing.end_time = datetime.now() + timedelta(days=1)

    if i != 2:
      borrowing.delivered = datetime.now() - timedelta(days=1)

    sql_session.add(borrowing)

  # Create at least one item that has been in the queue for so long that the queue position should expire
  queue_item = BookcaseItemBorrowingQueue(
    item=books[7],
    username='test_queue_user_expired',
  )
  queue_item.entered_queue_time = datetime.now() - timedelta(days=15)

  # Create at least one item that has been in the queue for so long that the queue position should expire,
  # but the queue person has already been notified
  queue_item = BookcaseItemBorrowingQueue(
    item=books[8],
    username='test_queue_user_expired_notified',
  )
  queue_item.entered_queue_time = datetime.now() - timedelta(days=15)

  sql_session.commit()

