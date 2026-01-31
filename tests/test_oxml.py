"""Unit tests for the OXML element classes in docx_revisions.oxml."""

import datetime as dt

import pytest
from docx.oxml.ns import qn
from docx.oxml.parser import parse_xml

import docx_revisions  # noqa: F401  — triggers element registration
from docx_revisions.oxml import (
    CT_PPrChange,
    CT_RPrChange,
    CT_RunTrackChange,
    CT_SectPrChange,
    CT_TblPrChange,
    CT_TcPrChange,
    CT_TrPrChange,
)

# -- helpers ---------------------------------------------------------------

_NSMAP = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def _ins_xml(attrs: str = "", children: str = "") -> str:
    return f"<w:ins {_NSMAP} {attrs}>{children}</w:ins>"


def _del_xml(attrs: str = "", children: str = "") -> str:
    return f"<w:del {_NSMAP} {attrs}>{children}</w:del>"


# -- CT_TrackChange --------------------------------------------------------


class DescribeCT_TrackChange:
    """Tests for CT_TrackChange base class (via w:ins registration)."""

    def it_reads_the_id_attribute(self):
        ins = parse_xml(_ins_xml('w:id="42" w:author="John"'))
        assert ins.id == 42

    def it_can_set_the_id_attribute(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John"'))
        ins.id = 99
        assert ins.id == 99

    def it_reads_the_author_attribute(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="Jane Doe"'))
        assert ins.author == "Jane Doe"

    def it_can_set_the_author_attribute(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John"'))
        ins.author = "Jane Doe"
        assert ins.author == "Jane Doe"

    def it_reads_the_date_attribute(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John" w:date="2024-01-15T10:30:00Z"'))
        assert ins.date == "2024-01-15T10:30:00Z"

    def it_returns_None_when_date_not_present(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John"'))
        assert ins.date is None

    def it_provides_date_value_as_datetime(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John" w:date="2024-01-15T10:30:00Z"'))
        d = ins.date_value
        assert d is not None
        assert d.year == 2024
        assert d.month == 1
        assert d.day == 15
        assert d.hour == 10
        assert d.minute == 30

    def it_returns_None_for_date_value_when_unset(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John"'))
        assert ins.date_value is None

    def it_can_set_date_value_from_datetime(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John"'))
        ins.date_value = dt.datetime(2024, 6, 15, 14, 30, 0, tzinfo=dt.timezone.utc)
        assert ins.date == "2024-06-15T14:30:00Z"

    def it_can_clear_date_value_by_setting_None(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="John" w:date="2024-01-15T10:30:00Z"'))
        ins.date_value = None
        assert ins.date is None


# -- CT_RunTrackChange -----------------------------------------------------


class DescribeCT_RunTrackChange:
    """Tests for CT_RunTrackChange (w:ins / w:del)."""

    def it_is_produced_by_parse_xml_for_w_ins(self):
        ins = parse_xml(_ins_xml('w:id="1" w:author="A"'))
        assert isinstance(ins, CT_RunTrackChange)

    def it_is_produced_by_parse_xml_for_w_del(self):
        d = parse_xml(_del_xml('w:id="1" w:author="A"'))
        assert isinstance(d, CT_RunTrackChange)

    def it_provides_paragraph_child_access(self):
        xml = _ins_xml('w:id="1" w:author="A"', "<w:p/><w:p/>")
        ins = parse_xml(xml)
        assert len(ins.p_lst) == 2

    def it_provides_run_child_access(self):
        xml = _ins_xml('w:id="1" w:author="A"', "<w:r/><w:r/><w:r/>")
        ins = parse_xml(xml)
        assert len(ins.r_lst) == 3

    def it_provides_inner_content_elements(self):
        xml = _ins_xml('w:id="1" w:author="A"', "<w:p/><w:tbl/><w:p/>")
        ins = parse_xml(xml)
        elements = ins.inner_content_elements
        assert len(elements) == 3
        assert elements[0].tag == qn("w:p")
        assert elements[1].tag == qn("w:tbl")
        assert elements[2].tag == qn("w:p")

    def it_provides_run_content_elements(self):
        xml = _ins_xml('w:id="1" w:author="A"', "<w:r/><w:r/>")
        ins = parse_xml(xml)
        elements = ins.run_content_elements
        assert len(elements) == 2
        assert elements[0].tag == qn("w:r")


# -- Element registration -------------------------------------------------


class DescribeElementRegistration:
    """Verify that registered elements produce the correct classes."""

    @pytest.mark.parametrize(
        ("tag", "expected_cls"),
        [
            ("rPrChange", CT_RPrChange),
            ("pPrChange", CT_PPrChange),
            ("sectPrChange", CT_SectPrChange),
            ("tblPrChange", CT_TblPrChange),
            ("tcPrChange", CT_TcPrChange),
            ("trPrChange", CT_TrPrChange),
        ],
    )
    def it_registers_the_element(self, tag: str, expected_cls: type):
        xml = f'<w:{tag} {_NSMAP} w:id="1" w:author="A"/>'
        elm = parse_xml(xml)
        assert isinstance(elm, expected_cls)
