"""Shared test fixtures for docx-revisions."""



from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
OXML_DOCX = TESTS_DIR / "OXML_TrackChanges_Test.docx"
TRICKY_DOCX = TESTS_DIR / "tricky-track-changes.docx"


@pytest.fixture
def oxml_docx_path() -> Path:
    """Path to the OXML track changes test document."""
    return OXML_DOCX


@pytest.fixture
def tricky_docx_path() -> Path:
    """Path to the tricky track changes test document."""
    return TRICKY_DOCX
