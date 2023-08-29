from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

@dataclass
class BookMetadata:
    isbn: str
    title: str
    authors: set[str]
    language: str
    publish_date: int
    num_pages: int
    subjects: set[str]