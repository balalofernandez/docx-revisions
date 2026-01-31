"""RevisionParagraph — a ``Paragraph`` subclass with track-change support.

Wraps an existing ``Paragraph`` (sharing the same XML element) and adds
methods for reading, creating, accepting, and rejecting tracked insertions
and deletions.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Iterator, List

from docx.oxml.ns import qn
from docx.oxml.parser import OxmlElement
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from docx_revisions._helpers import (
    make_del_element,
    make_ins_element,
    make_text_run,
    next_revision_id,
    revision_attrs,
    splice_tracked_replace,
)
from docx_revisions.revision import TrackedChange, TrackedDeletion, TrackedInsertion

if TYPE_CHECKING:
    from docx.styles.style import CharacterStyle


class RevisionParagraph(Paragraph):
    """A ``Paragraph`` subclass that adds track-change support.

    Create from an existing ``Paragraph`` with ``from_paragraph()`` — the
    two objects share the same underlying XML element so mutations via either
    reference are visible to both.

    Example:
        ```python
        from docx import Document
        from docx_revisions import RevisionParagraph

        doc = Document("example.docx")
        for para in doc.paragraphs:
            rp = RevisionParagraph.from_paragraph(para)
            if rp.has_track_changes:
                print(f"Insertions: {len(rp.insertions)}")
                print(f"Deletions:  {len(rp.deletions)}")
        ```
    """

    @classmethod
    def from_paragraph(cls, para: Paragraph) -> RevisionParagraph:
        """Create a ``RevisionParagraph`` that shares *para*'s XML element.

        Args:
            para: An existing ``Paragraph`` object.

        Returns:
            A ``RevisionParagraph`` wrapping the same ``<w:p>`` element.
        """
        return cls(para._p, para._parent)

    # ------------------------------------------------------------------
    # Read-only properties
    # ------------------------------------------------------------------

    @property
    def has_track_changes(self) -> bool:
        """True if this paragraph contains any ``w:ins`` or ``w:del`` children."""
        return bool(self._p.xpath("./w:ins | ./w:del"))

    @property
    def insertions(self) -> List[TrackedInsertion]:
        """All tracked insertions in this paragraph, in document order."""
        return [
            TrackedInsertion(e, self)  # pyright: ignore[reportArgumentType]
            for e in self._p.xpath("./w:ins")
        ]

    @property
    def deletions(self) -> List[TrackedDeletion]:
        """All tracked deletions in this paragraph, in document order."""
        return [
            TrackedDeletion(e, self)  # pyright: ignore[reportArgumentType]
            for e in self._p.xpath("./w:del")
        ]

    @property
    def track_changes(self) -> List[TrackedChange]:
        """All tracked changes (insertions and deletions) in document order."""
        changes: List[TrackedChange] = []
        for e in self._p.xpath("./w:ins | ./w:del"):
            tag = e.tag  # pyright: ignore[reportUnknownMemberType]
            if tag == qn("w:ins"):
                changes.append(TrackedInsertion(e, self))  # pyright: ignore[reportArgumentType]
            elif tag == qn("w:del"):
                changes.append(TrackedDeletion(e, self))  # pyright: ignore[reportArgumentType]
        return changes

    def _text_view(self, *, accept_changes: bool) -> str:
        """Return paragraph text with changes either accepted or rejected.

        Args:
            accept_changes: If True, include insertions and skip deletions
                (accepted view).  If False, include deletions and skip
                insertions (original/rejected view).
        """
        include_tag = qn("w:ins") if accept_changes else qn("w:del")
        parts: List[str] = []
        for element in self._p.xpath("./w:r | ./w:ins | ./w:del"):
            tag = element.tag  # pyright: ignore[reportUnknownMemberType]
            if tag == qn("w:r"):
                run = Run(element, self)
                parts.append(run.text)
            elif tag == include_tag:
                tracked = TrackedInsertion(element, self) if accept_changes else TrackedDeletion(element, self)  # pyright: ignore[reportArgumentType]
                parts.append(tracked.text)
        return "".join(parts)

    @property
    def accepted_text(self) -> str:
        """Text of this paragraph with all changes accepted.

        Insertions are kept, deletions are removed.
        """
        return self._text_view(accept_changes=True)

    @property
    def original_text(self) -> str:
        """Text of this paragraph with all changes rejected.

        Deletions are kept, insertions are removed.
        """
        return self._text_view(accept_changes=False)

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def iter_inner_content(  # type: ignore[override]
        self, include_revisions: bool = False
    ) -> Iterator[Run | Hyperlink | TrackedInsertion | TrackedDeletion]:
        """Generate runs, hyperlinks, and optionally revisions in document order.

        Args:
            include_revisions: If True, also yields ``TrackedInsertion`` and
                ``TrackedDeletion`` objects for run-level tracked changes.
                Defaults to False for backward compatibility.

        Yields:
            ``Run``, ``Hyperlink``, ``TrackedInsertion``, or ``TrackedDeletion``
            objects in document order.
        """
        if include_revisions:
            elements = self._p.xpath("./w:r | ./w:hyperlink | ./w:ins | ./w:del")
        else:
            elements = self._p.xpath("./w:r | ./w:hyperlink")

        for element in elements:
            tag = element.tag  # pyright: ignore[reportUnknownMemberType]
            if tag == qn("w:r"):
                yield Run(element, self)
            elif tag == qn("w:hyperlink"):
                yield Hyperlink(element, self)  # pyright: ignore[reportArgumentType]
            elif tag == qn("w:ins"):
                yield TrackedInsertion(element, self)  # pyright: ignore[reportArgumentType]
            elif tag == qn("w:del"):
                yield TrackedDeletion(element, self)  # pyright: ignore[reportArgumentType]

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_tracked_insertion(
        self,
        text: str | None = None,
        style: str | CharacterStyle | None = None,
        author: str = "",
        revision_id: int | None = None,
    ) -> TrackedInsertion:
        """Append a tracked insertion containing a run with the specified text.

        The run is wrapped in a ``w:ins`` element, marking it as inserted
        content when track changes is enabled.

        Args:
            text: Text to add to the run.
            style: Character style to apply to the run.
            author: Author name for the revision.  Defaults to empty string.
            revision_id: Unique ID for this revision.  Auto-generated if not
                provided.

        Returns:
            A ``TrackedInsertion`` wrapping the new ``w:ins`` element.

        Example:
            ```python
            rp = RevisionParagraph.from_paragraph(paragraph)
            tracked = rp.add_tracked_insertion("new text", author="Editor")
            print(tracked.text)
            ```
        """
        if revision_id is None:
            revision_id = self._next_revision_id()

        ins = OxmlElement(
            "w:ins",
            attrs=revision_attrs(revision_id, author, dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        )

        r = OxmlElement("w:r")
        ins.append(r)
        self._p.append(ins)  # pyright: ignore[reportUnknownMemberType]

        tracked_insertion = TrackedInsertion(ins, self)  # pyright: ignore[reportArgumentType]
        if text:
            for run in tracked_insertion.runs:
                run.text = text
        if style:
            for run in tracked_insertion.runs:
                run.style = style

        return tracked_insertion

    def add_tracked_deletion(
        self, start: int, end: int, author: str = "", revision_id: int | None = None
    ) -> TrackedDeletion:
        """Wrap existing text at *[start, end)* in a ``w:del`` element.

        The text remains in the document but is marked as deleted.  The
        corresponding ``w:t`` elements are converted to ``w:delText``.

        Args:
            start: Starting character offset (0-based, inclusive).
            end: Ending character offset (0-based, exclusive).
            author: Author name for the revision.
            revision_id: Unique ID for this revision.  Auto-generated if not
                provided.

        Returns:
            A ``TrackedDeletion`` wrapping the new ``w:del`` element.

        Raises:
            ValueError: If offsets are invalid.
        """
        para_text = self.text
        if start < 0 or end > len(para_text) or start >= end:
            raise ValueError(f"Invalid offsets: start={start}, end={end} for text of length {len(para_text)}")

        if revision_id is None:
            revision_id = self._next_revision_id()

        run_boundaries = self._get_run_boundaries()
        if not run_boundaries:
            raise ValueError("Paragraph has no runs")

        start_run_idx, start_offset = self._find_run_at_offset(run_boundaries, start)
        end_run_idx, end_offset = self._find_run_at_offset(run_boundaries, end)

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        runs = list(self.runs)

        # Collect the deleted text
        deleted_text_parts: List[str] = []
        if start_run_idx == end_run_idx:
            deleted_text_parts.append(runs[start_run_idx].text[start_offset:end_offset])
        else:
            deleted_text_parts.append(runs[start_run_idx].text[start_offset:])
            for i in range(start_run_idx + 1, end_run_idx):
                deleted_text_parts.append(runs[i].text)
            deleted_text_parts.append(runs[end_run_idx].text[:end_offset])
        deleted_text = "".join(deleted_text_parts)

        # Build the w:del element
        start_r = runs[start_run_idx]._r
        parent = start_r.getparent()
        if parent is None:
            raise ValueError("Run has no parent element")

        before_text = runs[start_run_idx].text[:start_offset]
        after_text = runs[end_run_idx].text[end_offset:]

        index = list(parent).index(start_r)
        for i in range(start_run_idx, end_run_idx + 1):
            run_elem = runs[i]._r
            if run_elem.getparent() is parent:
                parent.remove(run_elem)

        insert_idx = index

        if before_text:
            parent.insert(insert_idx, make_text_run(before_text))
            insert_idx += 1

        del_elem = make_del_element(deleted_text, author, revision_id, now)
        parent.insert(insert_idx, del_elem)
        insert_idx += 1

        if after_text:
            parent.insert(insert_idx, make_text_run(after_text))

        return TrackedDeletion(del_elem, self)  # pyright: ignore[reportArgumentType]

    def replace_tracked(self, search_text: str, replace_text: str, author: str = "", comment: str | None = None) -> int:
        """Replace all occurrences of *search_text* with *replace_text* using track changes.

        Each replacement creates a tracked deletion of *search_text* and a
        tracked insertion of *replace_text*.

        Args:
            search_text: Text to find and replace.
            replace_text: Text to insert in place of *search_text*.
            author: Author name for the revision.
            comment: Optional comment text (requires python-docx comment
                support).

        Returns:
            The number of replacements made.

        Example:
            ```python
            rp = RevisionParagraph.from_paragraph(paragraph)
            count = rp.replace_tracked("old", "new", author="Editor")
            ```
        """
        count = 0
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        runs = list(self.runs)
        for run in runs:
            text = run.text
            if search_text not in text:
                continue

            parts = text.split(search_text)

            r_elem = run._r
            parent = r_elem.getparent()
            if parent is None:
                continue
            index = list(parent).index(r_elem)

            parent.remove(r_elem)

            insert_idx = index
            for i, part in enumerate(parts):
                if part:
                    parent.insert(insert_idx, make_text_run(part))
                    insert_idx += 1

                if i < len(parts) - 1:
                    parent.insert(insert_idx, make_del_element(search_text, author, self._next_revision_id(), now))
                    insert_idx += 1

                    parent.insert(insert_idx, make_ins_element(replace_text, author, self._next_revision_id(), now))
                    insert_idx += 1

                    count += 1

        return count

    def replace_tracked_at(
        self, start: int, end: int, replace_text: str, author: str = "", comment: str | None = None
    ) -> None:
        """Replace text at character offsets *[start, end)* using track changes.

        Creates a tracked deletion of the text at positions ``[start, end)``
        and a tracked insertion of *replace_text* at that position.  The
        offsets are relative to ``paragraph.text``.

        Args:
            start: Starting character offset (0-based, inclusive).
            end: Ending character offset (0-based, exclusive).
            replace_text: Text to insert in place of the deleted text.
            author: Author name for the revision.
            comment: Optional comment text (requires python-docx comment
                support).

        Raises:
            ValueError: If *start* or *end* are out of bounds or *start* >= *end*.
        """
        para_text = self.text
        if start < 0 or end > len(para_text) or start >= end:
            raise ValueError(f"Invalid offsets: start={start}, end={end} for text of length {len(para_text)}")

        run_boundaries = self._get_run_boundaries()
        if not run_boundaries:
            raise ValueError("Paragraph has no runs")

        start_run_idx, start_offset_in_run = self._find_run_at_offset(run_boundaries, start)
        end_run_idx, end_offset_in_run = self._find_run_at_offset(run_boundaries, end)

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        runs = list(self.runs)

        # Compute the text splits
        if start_run_idx == end_run_idx:
            run = runs[start_run_idx]
            text = run.text
            before_text = text[:start_offset_in_run] or None
            deleted_text = text[start_offset_in_run:end_offset_in_run]
            after_text = text[end_offset_in_run:] or None
            first_r = run._r
        else:
            start_run = runs[start_run_idx]
            start_text = start_run.text
            before_text = start_text[:start_offset_in_run] or None
            deleted_from_start = start_text[start_offset_in_run:]

            end_run = runs[end_run_idx]
            end_text = end_run.text
            deleted_from_end = end_text[:end_offset_in_run]
            after_text = end_text[end_offset_in_run:] or None

            middle_deleted = "".join(runs[i].text for i in range(start_run_idx + 1, end_run_idx))
            deleted_text = deleted_from_start + middle_deleted + deleted_from_end
            first_r = start_run._r

        parent = first_r.getparent()
        if parent is None:
            return

        index = list(parent).index(first_r)

        # Remove spanned runs
        for i in range(start_run_idx, end_run_idx + 1):
            run_elem = runs[i]._r
            if run_elem.getparent() is parent:
                parent.remove(run_elem)

        splice_tracked_replace(
            parent, index, before_text, deleted_text, replace_text, after_text, author, self._next_revision_id, now
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _next_revision_id(self) -> int:
        """Generate the next unique revision ID for this document."""
        return next_revision_id(self._p)

    def _get_run_boundaries(self) -> List[tuple[int, int, int]]:
        """Return list of ``(run_index, start_offset, end_offset)`` for each run."""
        boundaries = []
        offset = 0
        for i, run in enumerate(self.runs):
            run_len = len(run.text)
            boundaries.append((i, offset, offset + run_len))
            offset += run_len
        return boundaries

    def _find_run_at_offset(self, boundaries: List[tuple[int, int, int]], offset: int) -> tuple[int, int]:
        """Find which run contains *offset* and the offset within that run."""
        for run_idx, run_start, run_end in boundaries:
            if run_start <= offset < run_end or (offset == run_end and run_idx == len(boundaries) - 1):
                return run_idx, offset - run_start
        last_idx, last_start, _ = boundaries[-1]
        return last_idx, offset - last_start
