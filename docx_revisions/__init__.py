"""docx-revisions: Track changes support for python-docx."""

from docx_revisions.models import Revision
from docx_revisions.revisions import (
    delete_with_tracking,
    get_accepted_text,
    get_revisions,
    insert_with_tracking,
    replace_with_tracking,
)

__version__ = "0.1.1"
__all__ = [
    "Revision",
    "get_accepted_text",
    "get_revisions",
    "insert_with_tracking",
    "delete_with_tracking",
    "replace_with_tracking",
]
