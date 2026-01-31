# AI Document Reviewer (pydantic-ai)

An AI agent that opens a Word document, reviews it, and writes edits back as
**tracked changes**, all powered by `docx-revisions` and
[pydantic-ai](https://ai.pydantic.dev/).

The full source lives in
[`examples/ai-chat/`](https://github.com/balalofernandez/docx-revisions/tree/main/examples/ai-chat).

## How it works

1. A `RevisionDocument` is loaded and passed to the agent as a dependency.
2. The agent reads every paragraph, decides what to change, and calls
   `replace_tracked()` or `add_tracked_insertion()` to write edits with full
   revision metadata.
3. The modified document is saved: open it in Word and you'll see the
   familiar red-line track changes.

## Agent definition

```python
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext

from docx_revisions import RevisionDocument

load_dotenv()

agent = Agent(
    "google-gla:gemini-2.5-flash",
    deps_type=RevisionDocument,
    system_prompt=(
        "You are a document reviewer. You have access to a Word document.\n"
        "1. First, call read_paragraphs to see the full document.\n"
        "2. Review the text and add track-change edits using write_with_track_changes.\n"
        "3. When you are done editing, call save_document to persist your changes.\n"
        "4. Return a short summary of what you changed."
    ),
)
```

## Tools

Three tools are registered on the agent:

**`read_paragraphs`**: returns every paragraph with its index number so the
agent knows what it's working with.

```python
@agent.tool
def read_paragraphs(ctx: RunContext[RevisionDocument]) -> str:
    """Return every paragraph in the document with its index number."""
    lines: list[str] = []
    for i, para in enumerate(ctx.deps.paragraphs):
        lines.append(f"[{i}] {para.text}")
    return "\n".join(lines)
```

**`write_with_track_changes`**: replaces text or appends an insertion as a
tracked change. The agent decides which paragraph to edit and what text to
find/replace.

```python
@agent.tool
def write_with_track_changes(
    ctx: RunContext[RevisionDocument],
    paragraph_index: int,
    search_text: str,
    new_text: str,
) -> str:
    """Add a tracked edit to a paragraph.

    If *search_text* is non-empty the matching text is replaced.
    If *search_text* is empty, *new_text* is appended as an insertion.
    """
    paras = ctx.deps.paragraphs
    if paragraph_index < 0 or paragraph_index >= len(paras):
        return f"Error: paragraph_index {paragraph_index} is out of range (0-{len(paras) - 1})."

    para = paras[paragraph_index]

    if search_text:
        count = para.replace_tracked(search_text, new_text, author="AI Reviewer")
        return f"Replaced {count} occurrence(s) of '{search_text}' in paragraph {paragraph_index}."

    para.add_tracked_insertion(text=new_text, author="AI Reviewer")
    return f"Inserted text at end of paragraph {paragraph_index}."
```

**`save_document`** — persists the document to disk.

```python
@agent.tool
def save_document(ctx: RunContext[RevisionDocument], path: str) -> str:
    """Save the document to *path*."""
    ctx.deps.save(path)
    return f"Document saved to {path}."
```

## Running the example

```bash
# 1. Set your API key
echo 'GOOGLE_API_KEY=your-key' > examples/ai-chat/.env

# 2. Run the agent
uv run --extra examples python examples/ai-chat/main.py

# 3. Verify the tracked changes were written
uv run --extra examples python examples/ai-chat/verificator.py
```

## Verifying the result

The verificator script opens the output document and checks that the AI's
edits actually appear as tracked insertions:

```python
from docx_revisions import RevisionDocument

rdoc = RevisionDocument("examples/ai-chat/license_reviewed.docx")
for para in rdoc.paragraphs:
    for ins in para.insertions:
        print(f"Author: {ins.author}, Text: {ins.text!r}")
```
