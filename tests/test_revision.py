"""Unit tests for TrackedInsertion and TrackedDeletion proxy classes."""



from unittest.mock import MagicMock

from docx.oxml.ns import qn
from docx.oxml.parser import parse_xml

import docx_revisions  # noqa: F401  — triggers element registration
from docx_revisions.revision import TrackedDeletion, TrackedInsertion

_NSMAP = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _make_parent() -> MagicMock:
    return MagicMock()


# -- TrackedInsertion -------------------------------------------------------


class DescribeTrackedInsertion:
    """Tests for TrackedInsertion proxy."""

    def it_reads_author(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="1" w:author="Alice"/>')
        tracked = TrackedInsertion(ins, _make_parent())
        assert tracked.author == "Alice"

    def it_can_set_author(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="1" w:author="Alice"/>')
        tracked = TrackedInsertion(ins, _make_parent())
        tracked.author = "Bob"
        assert tracked.author == "Bob"

    def it_reads_revision_id(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="42" w:author="Alice"/>')
        tracked = TrackedInsertion(ins, _make_parent())
        assert tracked.revision_id == 42

    def it_can_set_revision_id(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="1" w:author="Alice"/>')
        tracked = TrackedInsertion(ins, _make_parent())
        tracked.revision_id = 99
        assert tracked.revision_id == 99

    def it_reads_date(self):
        ins = parse_xml(
            f'<w:ins {_NSMAP} w:id="1" w:author="Alice"'
            f' w:date="2024-03-15T08:00:00Z"/>'
        )
        tracked = TrackedInsertion(ins, _make_parent())
        d = tracked.date
        assert d is not None
        assert d.year == 2024
        assert d.month == 3

    def it_detects_block_level_content(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="1" w:author="A"><w:p/></w:ins>')
        tracked = TrackedInsertion(ins, _make_parent())
        assert tracked.is_block_level is True
        assert tracked.is_run_level is False

    def it_detects_run_level_content(self):
        ins = parse_xml(f'<w:ins {_NSMAP} w:id="1" w:author="A"><w:r/></w:ins>')
        tracked = TrackedInsertion(ins, _make_parent())
        assert tracked.is_block_level is False
        assert tracked.is_run_level is True

    def it_provides_runs(self):
        ins = parse_xml(
            f'<w:ins {_NSMAP} w:id="1" w:author="A">'
            f"<w:r><w:t>Hello</w:t></w:r>"
            f"<w:r><w:t> World</w:t></w:r>"
            f"</w:ins>"
        )
        tracked = TrackedInsertion(ins, _make_parent())
        runs = tracked.runs
        assert len(runs) == 2

    def it_provides_text_for_run_level(self):
        ins = parse_xml(
            f'<w:ins {_NSMAP} w:id="1" w:author="A">'
            f"<w:r><w:t>Hello</w:t></w:r>"
            f"<w:r><w:t> World</w:t></w:r>"
            f"</w:ins>"
        )
        tracked = TrackedInsertion(ins, _make_parent())
        assert tracked.text == "Hello World"

    def it_accepts_by_unwrapping(self):
        body = parse_xml(
            f'<w:body {_NSMAP}>'
            f"<w:p/>"
            f'<w:ins w:id="1" w:author="A"><w:r><w:t>inserted</w:t></w:r></w:ins>'
            f"<w:p/>"
            f"</w:body>"
        )
        ins_elm = body[1]
        tracked = TrackedInsertion(ins_elm, _make_parent())
        tracked.accept()

        # The w:ins wrapper should be gone; the w:r should be direct child of body
        tags = [child.tag for child in body]
        assert qn("w:ins") not in tags
        assert qn("w:r") in tags

    def it_rejects_by_removing_entirely(self):
        body = parse_xml(
            f'<w:body {_NSMAP}>'
            f"<w:p/>"
            f'<w:ins w:id="1" w:author="A"><w:r><w:t>inserted</w:t></w:r></w:ins>'
            f"<w:p/>"
            f"</w:body>"
        )
        ins_elm = body[1]
        tracked = TrackedInsertion(ins_elm, _make_parent())
        tracked.reject()

        tags = [child.tag for child in body]
        assert qn("w:ins") not in tags
        assert len(list(body)) == 2  # only the two w:p elements remain


# -- TrackedDeletion --------------------------------------------------------


class DescribeTrackedDeletion:
    """Tests for TrackedDeletion proxy."""

    def it_reads_author(self):
        d = parse_xml(f'<w:del {_NSMAP} w:id="1" w:author="Bob"/>')
        tracked = TrackedDeletion(d, _make_parent())
        assert tracked.author == "Bob"

    def it_reads_revision_id(self):
        d = parse_xml(f'<w:del {_NSMAP} w:id="55" w:author="Bob"/>')
        tracked = TrackedDeletion(d, _make_parent())
        assert tracked.revision_id == 55

    def it_detects_run_level_content(self):
        d = parse_xml(f'<w:del {_NSMAP} w:id="1" w:author="B"><w:r/></w:del>')
        tracked = TrackedDeletion(d, _make_parent())
        assert tracked.is_run_level is True
        assert tracked.is_block_level is False

    def it_reads_text_from_delText(self):
        d = parse_xml(
            f'<w:del {_NSMAP} w:id="1" w:author="B">'
            f"<w:r><w:delText>deleted text</w:delText></w:r>"
            f"</w:del>"
        )
        tracked = TrackedDeletion(d, _make_parent())
        assert tracked.text == "deleted text"

    def it_reads_text_from_w_t_as_fallback(self):
        d = parse_xml(
            f'<w:del {_NSMAP} w:id="1" w:author="B">'
            f"<w:r><w:t>deleted via t</w:t></w:r>"
            f"</w:del>"
        )
        tracked = TrackedDeletion(d, _make_parent())
        assert tracked.text == "deleted via t"

    def it_accepts_by_removing_entirely(self):
        body = parse_xml(
            f'<w:body {_NSMAP}>'
            f"<w:p/>"
            f'<w:del w:id="1" w:author="B"><w:r><w:t>deleted</w:t></w:r></w:del>'
            f"<w:p/>"
            f"</w:body>"
        )
        del_elm = body[1]
        tracked = TrackedDeletion(del_elm, _make_parent())
        tracked.accept()

        tags = [child.tag for child in body]
        assert qn("w:del") not in tags
        assert len(list(body)) == 2

    def it_rejects_by_unwrapping(self):
        body = parse_xml(
            f'<w:body {_NSMAP}>'
            f"<w:p/>"
            f'<w:del w:id="1" w:author="B"><w:r><w:t>deleted</w:t></w:r></w:del>'
            f"<w:p/>"
            f"</w:body>"
        )
        del_elm = body[1]
        tracked = TrackedDeletion(del_elm, _make_parent())
        tracked.reject()

        tags = [child.tag for child in body]
        assert qn("w:del") not in tags
        assert qn("w:r") in tags

    def it_converts_delText_to_t_on_reject(self):
        body = parse_xml(
            f'<w:body {_NSMAP}>'
            f'<w:del w:id="1" w:author="B">'
            f"<w:r><w:delText>text</w:delText></w:r>"
            f"</w:del>"
            f"</w:body>"
        )
        del_elm = body[0]
        tracked = TrackedDeletion(del_elm, _make_parent())
        tracked.reject()

        # After rejection, w:delText should be converted to w:t
        r_elem = body[0]
        t_elems = r_elem.findall(qn("w:t"))
        del_text_elems = r_elem.findall(qn("w:delText"))
        assert len(t_elems) == 1
        assert len(del_text_elems) == 0
        assert t_elems[0].text == "text"
