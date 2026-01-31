"""Shared XML element builders for revision tracking.

Centralises the repeated patterns for creating ``w:r``, ``w:del``, ``w:ins``
elements and the ``before / del / ins / after`` splice used by both
``RevisionParagraph`` and ``RevisionRun``.
"""

from __future__ import annotations

import contextlib
from typing import Callable

from docx.oxml.ns import qn
from docx.oxml.parser import OxmlElement
from lxml import etree


def revision_attrs(rev_id: int, author: str, now: str) -> dict[str, str]:
    """Build the standard ``{w:id, w:author, w:date}`` attribute dict."""
    return {qn("w:id"): str(rev_id), qn("w:author"): author, qn("w:date"): now}


def make_text_run(text: str) -> OxmlElement:
    """Create a ``<w:r><w:t>text</w:t></w:r>`` element with space preservation."""
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = text
    if text.startswith(" ") or text.endswith(" "):
        t.set(qn("xml:space"), "preserve")
    r.append(t)
    return r


def make_del_element(deleted_text: str, author: str, rev_id: int, now: str) -> OxmlElement:
    """Create a ``<w:del><w:r><w:delText>text</w:delText></w:r></w:del>`` element."""
    del_elem = OxmlElement("w:del", attrs=revision_attrs(rev_id, author, now))
    del_r = OxmlElement("w:r")
    del_text_elem = OxmlElement("w:delText")
    del_text_elem.text = deleted_text
    del_r.append(del_text_elem)
    del_elem.append(del_r)
    return del_elem


def make_ins_element(insert_text: str, author: str, rev_id: int, now: str) -> OxmlElement:
    """Create a ``<w:ins><w:r><w:t>text</w:t></w:r></w:ins>`` element."""
    ins_elem = OxmlElement("w:ins", attrs=revision_attrs(rev_id, author, now))
    ins_r = OxmlElement("w:r")
    ins_t = OxmlElement("w:t")
    ins_t.text = insert_text
    ins_r.append(ins_t)
    ins_elem.append(ins_r)
    return ins_elem


def splice_tracked_replace(
    parent: etree._Element,
    index: int,
    before_text: str | None,
    deleted_text: str,
    insert_text: str,
    after_text: str | None,
    author: str,
    next_id_fn: Callable[[], int],
    now: str,
) -> int:
    """Insert the before-run / w:del / w:ins / after-run sequence into *parent* at *index*.

    Returns:
        The number of elements inserted.
    """
    insert_idx = index
    if before_text:
        parent.insert(insert_idx, make_text_run(before_text))
        insert_idx += 1

    parent.insert(insert_idx, make_del_element(deleted_text, author, next_id_fn(), now))
    insert_idx += 1

    parent.insert(insert_idx, make_ins_element(insert_text, author, next_id_fn(), now))
    insert_idx += 1

    if after_text:
        parent.insert(insert_idx, make_text_run(after_text))
        insert_idx += 1

    return insert_idx - index


def next_revision_id(element: etree._Element) -> int:
    """Generate the next unique revision ID by scanning the document tree from *element*."""
    max_id = 0
    for ins_or_del in element.xpath("//w:ins | //w:del"):
        id_val = ins_or_del.get(qn("w:id"))
        if id_val is not None:
            with contextlib.suppress(ValueError):
                max_id = max(max_id, int(id_val))
    return max_id + 1
