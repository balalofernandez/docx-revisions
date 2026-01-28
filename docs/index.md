# docx-revisions

**Track changes and document revision support for Word documents (.docx) in Python.** docx-revisions extends python-docx to read and write **OOXML** revision markup (insertions and deletions) so you can work with **Microsoft Word** track changes, revision metadata (author, date), and accepted text programmatically.

## Installation

```bash
pip install docx-revisions
```

## Quick Start

```python
from docx import Document
from docx_revisions import get_accepted_text, get_revisions, insert_with_tracking

doc = Document("tracked_changes.docx")
p = doc.paragraphs[0]

# Get text with all changes accepted
text = get_accepted_text(p)

# List all revisions
for rev in get_revisions(p):
    print(f"{rev.type}: '{rev.text}' by {rev.author}")

# Add tracked insertion
insert_with_tracking(p, " new text", author="Agent")
doc.save("output.docx")
```

Use docx-revisions to **parse DOCX files** with track changes on, get **accepted text** (all insertions applied, deletions removed), list **revisions** (insertions and deletions) with author and date, or **write new revisions** (insert, delete, replace) that appear as track changes in Word. Built on python-docx and **OOXML** (Office Open XML); works with **.docx** and **revision tracking** metadata.

## API reference

::: docx_revisions
