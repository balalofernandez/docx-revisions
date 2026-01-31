"""docx-revisions: Track changes support for python-docx."""

from importlib.metadata import version

from docx_revisions.document import RevisionDocument
from docx_revisions.oxml import register_revision_elements
from docx_revisions.paragraph import RevisionParagraph
from docx_revisions.revision import TrackedChange, TrackedDeletion, TrackedInsertion
from docx_revisions.run import RevisionRun

# Register OXML element classes so lxml produces typed instances
# for w:ins, w:del, w:delText, etc.
register_revision_elements()

__version__ = version("docx-revisions")
__all__ = [
    "RevisionDocument",
    "RevisionParagraph",
    "RevisionRun",
    "TrackedChange",
    "TrackedDeletion",
    "TrackedInsertion",
]
