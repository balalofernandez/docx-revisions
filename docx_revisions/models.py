"""Data models for track changes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Revision:
    """Represents a single revision (insertion or deletion) in a paragraph.

    Attributes:
        type: The type of revision - "ins" for insertion, "del" for deletion.
        text: The text content of the revision.
        author: The author who made the revision.
        date: The timestamp when the revision was made.
    """

    type: Literal["ins", "del"]
    text: str
    author: str
    date: datetime | None = None
