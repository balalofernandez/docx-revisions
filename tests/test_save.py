"""Tests for RevisionDocument.save accepting paths and file-like objects."""

import io
from pathlib import Path

from docx import Document

from docx_revisions import RevisionDocument


class DescribeRevisionDocument_save_targets:
    """save() should accept str paths, Path objects, and binary streams."""

    def it_saves_to_bytesio_and_roundtrips(self):
        doc = Document()
        doc.add_paragraph("Hello BytesIO")
        rdoc = RevisionDocument(doc)

        buffer = io.BytesIO()
        rdoc.save(buffer)

        assert buffer.tell() > 0
        buffer.seek(0)

        rdoc2 = RevisionDocument(buffer)
        texts = [p.text for p in rdoc2.document.paragraphs]
        assert "Hello BytesIO" in texts

    def it_saves_to_string_path(self, tmp_path: Path):
        rdoc = RevisionDocument()
        path = tmp_path / "saved_str.docx"
        rdoc.save(str(path))
        assert path.exists()

        rdoc2 = RevisionDocument(str(path))
        assert rdoc2.document is not None

    def it_saves_to_path_object(self, tmp_path: Path):
        rdoc = RevisionDocument()
        path = tmp_path / "saved_path.docx"
        rdoc.save(path)
        assert path.exists()

        rdoc2 = RevisionDocument(str(path))
        assert rdoc2.document is not None
