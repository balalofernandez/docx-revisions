"""RevisionRun — a ``Run`` subclass with track-change support.

Wraps an existing ``Run`` (sharing the same XML element) and adds methods
for creating tracked deletions and offset-based replacements.
"""

from __future__ import annotations

import datetime as dt

from docx.oxml.ns import qn
from docx.oxml.parser import OxmlElement
from docx.text.run import Run

from docx_revisions._helpers import next_revision_id, revision_attrs, splice_tracked_replace
from docx_revisions.revision import TrackedDeletion


class RevisionRun(Run):
    """A ``Run`` subclass that adds track-change support.

    Create from an existing ``Run`` with ``from_run()`` — the two objects
    share the same underlying XML element.

    Example:
        ```python
        from docx_revisions import RevisionRun

        run = paragraph.runs[0]
        rr = RevisionRun.from_run(run)
        tracked = rr.delete_tracked(author="Editor")
        ```
    """

    @classmethod
    def from_run(cls, run: Run) -> RevisionRun:
        """Create a ``RevisionRun`` that shares *run*'s XML element.

        Args:
            run: An existing ``Run`` object.

        Returns:
            A ``RevisionRun`` wrapping the same ``<w:r>`` element.
        """
        return cls(run._r, run._parent)

    def delete_tracked(self, author: str = "", revision_id: int | None = None) -> TrackedDeletion:
        """Mark this run as deleted with track changes.

        Instead of removing the run, it is wrapped in a ``w:del`` element to
        mark it as deleted content.  The run remains in the document but is
        displayed as deleted text (e.g., with strikethrough).  The ``w:t``
        elements are converted to ``w:delText``.

        Args:
            author: Author name for the revision.
            revision_id: Unique ID for this revision.  Auto-generated if not
                provided.

        Returns:
            A ``TrackedDeletion`` wrapping the ``w:del`` element.

        Raises:
            ValueError: If the run has no parent element.
        """
        if revision_id is None:
            revision_id = self._next_revision_id()

        parent = self._r.getparent()
        if parent is None:
            raise ValueError("Run has no parent element")

        del_elem = OxmlElement(
            "w:del",
            attrs=revision_attrs(
                revision_id,
                author,
                dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )

        for t_elem in self._r.findall(qn("w:t")):
            delText = OxmlElement("w:delText")
            delText.text = t_elem.text
            if t_elem.get(qn("xml:space")) == "preserve":
                delText.set(qn("xml:space"), "preserve")
            t_elem.getparent().replace(t_elem, delText)  # pyright: ignore[reportOptionalMemberAccess]

        index = list(parent).index(self._r)
        parent.insert(index, del_elem)
        del_elem.append(self._r)

        return TrackedDeletion(del_elem, self._parent)  # pyright: ignore[reportArgumentType]

    def replace_tracked_at(
        self,
        start: int,
        end: int,
        replace_text: str,
        author: str = "",
    ) -> None:
        """Replace text at character offsets *[start, end)* using track changes.

        Creates a tracked deletion of the text at positions ``[start, end)``
        and a tracked insertion of *replace_text* at that position.

        Args:
            start: Starting character offset (0-based, inclusive).
            end: Ending character offset (0-based, exclusive).
            replace_text: Text to insert in place of the deleted text.
            author: Author name for the revision.

        Raises:
            ValueError: If *start* or *end* are out of bounds or *start* >= *end*.
        """
        text = self.text
        if start < 0 or end > len(text) or start >= end:
            raise ValueError(
                f"Invalid offsets: start={start}, end={end} for text of length {len(text)}"
            )

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        before_text = text[:start] or None
        deleted_text = text[start:end]
        after_text = text[end:] or None

        r_elem = self._r
        parent = r_elem.getparent()
        if parent is None:
            raise ValueError("Run has no parent element")

        index = list(parent).index(r_elem)
        parent.remove(r_elem)

        splice_tracked_replace(
            parent,
            index,
            before_text,
            deleted_text,
            replace_text,
            after_text,
            author,
            self._next_revision_id,
            now,
        )

    def _next_revision_id(self) -> int:
        """Generate the next unique revision ID for this document."""
        return next_revision_id(self._r)
