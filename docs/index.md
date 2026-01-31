# Python Track Changes Library for Word Documents

**Read and write track changes in Word documents (.docx) with Python.** docx-revisions is a Python library that extends python-docx to support **Microsoft Word track changes** and **document revisions** — OOXML revision markup (insertions and deletions) — so you can programmatically accept text, list revisions with author and date, and apply insertions, deletions, or replacements with full revision metadata.

## Installation

```bash
pip install docx-revisions
```
or
```bash
uv add docx-revisions
```

## Quick Start

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

## API reference

::: docx_revisions
