# Python Tracked Changes Library - docx-revisions

<p align="center">
  <a href="https://balalofernandez.github.io/docx-revisions" target="_blank"><img src="https://img.shields.io/badge/Docs-0066FF" alt="Documentation"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml/badge.svg" alt="Docs"></a>
  <a href="https://pypi.org/project/docx-revisions" target="_blank"><img src="https://img.shields.io/pypi/v/docx-revisions" alt="PyPI"></a>
  <!-- <a href="https://pepy.tech/projects/docx-revisions"><img src="https://static.pepy.tech/badge/docx-revisions" alt="PyPI Downloads"></a> -->
</p>

**Read and write track changes in Word documents (.docx) with Python.** docx-revisions extends [python-docx](https://python-docx.readthedocs.io/) to support **document revision tracking**, **change tracking**, and **OOXML** revision markup (insertions `<w:ins>` and deletions `<w:del>`) so you can programmatically accept text, list revisions with author and date, and apply insertions, deletions, or replacements with full revision metadata.

Use it for **Microsoft Word**-compatible revision tracking: parse DOCX files with track changes on, get accepted (clean) text, enumerate revisions per paragraph, or write new revisions (insert/delete/replace) that show up as track changes in Word.

## Installation

```bash
pip install docx-revisions
```

## Quick Start

### Check out our examples!

Navigate to the [examples directory](https://github.com/balalofernandez/docx-revisions/tree/main/examples) to see code samples.

### Read tracked changes

```python
from docx_revisions import RevisionDocument

rdoc = RevisionDocument("tracked_changes.docx")
for para in rdoc.paragraphs:
    if para.has_track_changes:
        for change in para.track_changes:
            print(f"{type(change).__name__}: '{change.text}' by {change.author}")
        print(f"Accepted: {para.accepted_text}")
        print(f"Original: {para.original_text}")
```

### Accept or reject all changes

```python
from docx_revisions import RevisionDocument

rdoc = RevisionDocument("tracked_changes.docx")
rdoc.accept_all()   # or rdoc.reject_all()
rdoc.save("clean.docx")
```

### Find and replace with tracking

```python
from docx_revisions import RevisionDocument

rdoc = RevisionDocument("contract.docx")
count = rdoc.find_and_replace_tracked("Acme Corp", "NewCo Inc", author="Legal")
print(f"Replaced {count} occurrences")
rdoc.save("contract_revised.docx")
```

### Add tracked insertions and deletions

```python
from docx_revisions import RevisionParagraph

rp = RevisionParagraph.from_paragraph(paragraph)
rp.add_tracked_insertion("new text", author="Editor")
rp.add_tracked_deletion(start=5, end=10, author="Editor")
```
