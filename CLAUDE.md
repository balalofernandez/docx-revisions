# Documentation (docx-revisions)

- **Docstrings:** Use Google-style (Args, Returns, Example, etc.).
- **Examples:** Put code in a **Markdown fenced block** inside the Example section:
  - Use ` ```python ` … ` ``` ` (not doctest `>>>`), so the docs site renders a real code block with a copy button.
- **Public API:** Document every public function/class with a short summary, Args/Returns, and an Example where useful.
- **Docs site:** MkDocs + Material + mkdocstrings; build with `uv run mkdocs build`, serve with `uv run mkdocs serve`.
