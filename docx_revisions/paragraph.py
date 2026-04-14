"""RevisionParagraph — a ``Paragraph`` subclass with track-change support.

Wraps an existing ``Paragraph`` (sharing the same XML element) and adds
methods for reading, creating, accepting, and rejecting tracked insertions
and deletions.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Iterator, List, Literal

from docx.oxml.ns import qn
from docx.oxml.parser import OxmlElement
from docx.text.hyperlink import Hyperlink
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from lxml import etree

from docx_revisions._helpers import (
    make_del_element,
    make_text_run,
    next_revision_id,
    revision_attrs,
    splice_tracked_replace,
)
from docx_revisions.revision import TrackedChange, TrackedDeletion, TrackedInsertion

if TYPE_CHECKING:
    from docx.styles.style import CharacterStyle

IndexMode = Literal["text", "accepted", "original"]


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
        skip_tag = qn("w:del") if accept_changes else qn("w:ins")

        def walk(element: etree._Element) -> str:
            parts: List[str] = []
            for child in element.xpath("./w:r | ./w:ins | ./w:del"):
                tag = child.tag
                if tag == qn("w:r"):
                    for t in child.xpath("./w:t | ./w:delText"):
                        parts.append(t.text or "")
                elif tag == include_tag:
                    parts.append(walk(child))
                elif tag == skip_tag:
                    continue
            return "".join(parts)

        return walk(self._p)

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
        self, start: int, end: int, author: str = "", revision_id: int | None = None, index_mode: IndexMode = "text"
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
            index_mode: Which text view the offsets index into:
                ``"text"`` (default, raw ``paragraph.text`` ignoring prior
                revisions), ``"accepted"`` (``paragraph.accepted_text``, with
                prior insertions kept and deletions skipped), or
                ``"original"`` (``paragraph.original_text``, with prior
                deletions kept and insertions skipped).

        Returns:
            A ``TrackedDeletion`` wrapping the new ``w:del`` element.

        Raises:
            ValueError: If offsets are invalid.

        Example:
            ```python
            # Delete characters from the accepted (post-revision) view
            rp.add_tracked_deletion(0, 5, author="Editor", index_mode="accepted")
            ```
        """
        view_text = self._view_text(index_mode)
        if start < 0 or end > len(view_text) or start >= end:
            raise ValueError(f"Invalid offsets: start={start}, end={end} for text of length {len(view_text)}")

        if revision_id is None:
            revision_id = self._next_revision_id()

        units = self._get_editable_units(index_mode)
        if not units:
            raise ValueError("Paragraph has no runs")
        boundaries = self._unit_boundaries(units)

        start_unit_idx, start_offset = self._find_unit_at_offset(boundaries, start)
        end_unit_idx, end_offset = self._find_unit_at_offset(boundaries, end)

        # All units in the [start, end) span must share the same parent for a
        # clean single-parent splice.  This holds when the span is entirely in
        # top-level w:r runs, or entirely inside one w:ins / w:del wrapper.
        start_parent = units[start_unit_idx].getparent()
        end_parent = units[end_unit_idx].getparent()
        if start_parent is None or start_parent is not end_parent:
            raise ValueError(
                "Cannot apply tracked deletion across a revision boundary; "
                "operate on a narrower span entirely inside or outside a prior revision."
            )
        parent = start_parent

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def _r_text(r: etree._Element) -> str:
            parts = []
            for child in r.xpath("./w:t | ./w:delText"):
                parts.append(child.text or "")
            return "".join(parts)

        # Collect the deleted text
        deleted_text_parts: List[str] = []
        if start_unit_idx == end_unit_idx:
            deleted_text_parts.append(_r_text(units[start_unit_idx])[start_offset:end_offset])
        else:
            deleted_text_parts.append(_r_text(units[start_unit_idx])[start_offset:])
            for i in range(start_unit_idx + 1, end_unit_idx):
                deleted_text_parts.append(_r_text(units[i]))
            deleted_text_parts.append(_r_text(units[end_unit_idx])[:end_offset])
        deleted_text = "".join(deleted_text_parts)

        start_r = units[start_unit_idx]
        before_text = _r_text(start_r)[:start_offset]
        after_text = _r_text(units[end_unit_idx])[end_offset:]

        index = list(parent).index(start_r)
        for i in range(start_unit_idx, end_unit_idx + 1):
            run_elem = units[i]
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

    def replace_tracked(
        self,
        search_text: str,
        replace_text: str,
        author: str = "",
        comment: str | None = None,
        index_mode: IndexMode = "text",
    ) -> int:
        """Replace all occurrences of *search_text* with *replace_text* using track changes.

        Each replacement creates a tracked deletion of *search_text* and a
        tracked insertion of *replace_text*.  Matches text across run
        boundaries (handles OOXML run splitting).

        Args:
            search_text: Text to find and replace.
            replace_text: Text to insert in place of *search_text*.
            author: Author name for the revision.
            comment: Optional comment text (requires python-docx comment
                support).
            index_mode: Which text view to search against:
                ``"text"`` (default, raw ``paragraph.text``),
                ``"accepted"`` (``paragraph.accepted_text``, includes prior
                insertions, skips prior deletions), or ``"original"``
                (``paragraph.original_text``, includes prior deletions, skips
                prior insertions).

        Returns:
            The number of replacements made.

        Example:
            ```python
            # Default: search raw run text
            rp.replace_tracked("old", "new", author="Editor")

            # Search the accepted view — matches land inside prior w:ins blocks
            rp.replace_tracked(
                "old", "new", author="Editor", index_mode="accepted"
            )
            ```
        """
        count = 0
        full_text = self._view_text(index_mode)
        search_len = len(search_text)

        # Find all match positions in the concatenated text.
        # Process right-to-left so earlier offsets stay valid after each splice.
        positions: list[int] = []
        start = 0
        while True:
            idx = full_text.find(search_text, start)
            if idx == -1:
                break
            positions.append(idx)
            start = idx + search_len

        # Apply replacements right-to-left to preserve offsets.
        for pos in reversed(positions):
            self.replace_tracked_at(
                pos, pos + search_len, replace_text, author=author, comment=comment, index_mode=index_mode
            )
            count += 1

        return count

    def replace_tracked_at(
        self,
        start: int,
        end: int,
        replace_text: str,
        author: str = "",
        comment: str | None = None,
        index_mode: IndexMode = "text",
    ) -> None:
        """Replace text at character offsets *[start, end)* using track changes.

        Creates a tracked deletion of the text at positions ``[start, end)``
        and a tracked insertion of *replace_text* at that position.

        Args:
            start: Starting character offset (0-based, inclusive).
            end: Ending character offset (0-based, exclusive).
            replace_text: Text to insert in place of the deleted text.
            author: Author name for the revision.
            comment: Optional comment text (requires python-docx comment
                support).
            index_mode: Which text view the offsets index into.  See
                :meth:`replace_tracked`.

        Raises:
            ValueError: If *start* or *end* are out of bounds or *start* >= *end*.

        Example:
            ```python
            # Offsets are interpreted against accepted_text
            rp.replace_tracked_at(
                0, 5, "Hi", author="Editor", index_mode="accepted"
            )
            ```
        """
        view_text = self._view_text(index_mode)
        if start < 0 or end > len(view_text) or start >= end:
            raise ValueError(f"Invalid offsets: start={start}, end={end} for text of length {len(view_text)}")

        units = self._get_editable_units(index_mode)
        if not units:
            raise ValueError("Paragraph has no runs")
        boundaries = self._unit_boundaries(units)

        start_unit_idx, start_offset_in_unit = self._find_unit_at_offset(boundaries, start)
        end_unit_idx, end_offset_in_unit = self._find_unit_at_offset(boundaries, end)

        start_parent = units[start_unit_idx].getparent()
        end_parent = units[end_unit_idx].getparent()
        if start_parent is None or start_parent is not end_parent:
            raise ValueError(
                "Cannot apply tracked replacement across a revision boundary; "
                "operate on a narrower span entirely inside or outside a prior revision."
            )
        parent = start_parent

        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        def _r_text(r: etree._Element) -> str:
            parts = []
            for child in r.xpath("./w:t | ./w:delText"):
                parts.append(child.text or "")
            return "".join(parts)

        if start_unit_idx == end_unit_idx:
            r = units[start_unit_idx]
            text = _r_text(r)
            before_text = text[:start_offset_in_unit] or None
            deleted_text = text[start_offset_in_unit:end_offset_in_unit]
            after_text = text[end_offset_in_unit:] or None
            first_r = r
        else:
            first_r = units[start_unit_idx]
            start_text = _r_text(first_r)
            before_text = start_text[:start_offset_in_unit] or None
            deleted_from_start = start_text[start_offset_in_unit:]

            end_r = units[end_unit_idx]
            end_text = _r_text(end_r)
            deleted_from_end = end_text[:end_offset_in_unit]
            after_text = end_text[end_offset_in_unit:] or None

            middle_deleted = "".join(_r_text(units[i]) for i in range(start_unit_idx + 1, end_unit_idx))
            deleted_text = deleted_from_start + middle_deleted + deleted_from_end

        index = list(parent).index(first_r)

        # Remove spanned runs (only if they share the parent, which the check above guarantees)
        for i in range(start_unit_idx, end_unit_idx + 1):
            run_elem = units[i]
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

    def _view_text(self, index_mode: IndexMode) -> str:
        """Return the paragraph text for the chosen index mode."""
        if index_mode == "text":
            return self.text
        if index_mode == "accepted":
            return self.accepted_text
        if index_mode == "original":
            return self.original_text
        raise ValueError(f"Unknown index_mode: {index_mode!r}")

    def _get_editable_units(self, index_mode: IndexMode) -> List[etree._Element]:
        """Return the ordered list of ``w:r`` elements that make up *index_mode*'s view.

        - ``"text"``: only top-level ``w:r`` children.
        - ``"accepted"``: walk ``w:r`` children, recurse into ``w:ins``
          (prior insertions visible), skip ``w:del``.
        - ``"original"``: walk ``w:r`` children, recurse into ``w:del``
          (prior deletions visible), skip ``w:ins``.
        """
        if index_mode == "text":
            return list(self._p.xpath("./w:r"))

        if index_mode == "accepted":
            recurse_tag = qn("w:ins")
            skip_tag = qn("w:del")
        elif index_mode == "original":
            recurse_tag = qn("w:del")
            skip_tag = qn("w:ins")
        else:
            raise ValueError(f"Unknown index_mode: {index_mode!r}")

        units: List[etree._Element] = []

        def walk(element: etree._Element) -> None:
            for child in element.xpath("./w:r | ./w:ins | ./w:del"):
                tag = child.tag
                if tag == qn("w:r"):
                    units.append(child)
                elif tag == recurse_tag:
                    walk(child)
                elif tag == skip_tag:
                    continue

        walk(self._p)
        return units

    @staticmethod
    def _unit_boundaries(units: List[etree._Element]) -> List[tuple[int, int, int]]:
        """Return ``(unit_index, start_offset, end_offset)`` for each unit."""
        boundaries: List[tuple[int, int, int]] = []
        offset = 0
        for i, r in enumerate(units):
            # Sum text from both w:t and w:delText direct children
            run_len = 0
            for child in r.xpath("./w:t | ./w:delText"):
                run_len += len(child.text or "")
            boundaries.append((i, offset, offset + run_len))
            offset += run_len
        return boundaries

    @staticmethod
    def _find_unit_at_offset(boundaries: List[tuple[int, int, int]], offset: int) -> tuple[int, int]:
        """Find which unit contains *offset* and the offset within that unit."""
        for unit_idx, unit_start, unit_end in boundaries:
            if unit_start <= offset < unit_end or (offset == unit_end and unit_idx == len(boundaries) - 1):
                return unit_idx, offset - unit_start
        last_idx, last_start, _ = boundaries[-1]
        return last_idx, offset - last_start

    # Back-compat aliases (used by older external code or tests that may import them)
    def _get_run_boundaries(self) -> List[tuple[int, int, int]]:
        """Deprecated: use :meth:`_get_editable_units` + :meth:`_unit_boundaries`."""
        return self._unit_boundaries(self._get_editable_units("text"))

    def _find_run_at_offset(self, boundaries: List[tuple[int, int, int]], offset: int) -> tuple[int, int]:
        """Deprecated: use :meth:`_find_unit_at_offset`."""
        return self._find_unit_at_offset(boundaries, offset)
