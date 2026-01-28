# docx-revisions

Track changes support for python-docx.

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


::: docx_revisions
