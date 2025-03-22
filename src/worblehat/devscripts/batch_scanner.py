from worblehat.models import Bookcase

# TODO: keep state about the currently chosen shelf
def main(sql_session) -> None:
  ...
  # while True:
  #   isbn = input("Waiting for new ISBN> ")
  #   print(f"Scanned ISBN: {isbn}")

def add_new_book(
  sql_session,
  isbn: str,
  bookcase: Bookcase,
) -> None:
  ...
