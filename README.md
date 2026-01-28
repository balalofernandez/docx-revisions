# docx-revisions

<p align="center">
  <a href="https://balalofernandez.github.io/docx-revisions" target="_blank"><img src="https://img.shields.io/badge/Docs-0066FF" alt="Documentation"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml/badge.svg" alt="Docs"></a>
  <a href="https://pypi.org/project/docx-revisions" target="_blank"><img src="https://img.shields.io/pypi/v/docx-revisions" alt="PyPI"></a>
  <!-- <a href="https://pepy.tech/projects/docx-revisions"><img src="https://static.pepy.tech/badge/docx-revisions" alt="PyPI Downloads"></a> -->
</p>

**Read and write track changes in Word documents (.docx) with Python.** docx-revisions extends [python-docx](https://python-docx.readthedocs.io/) to support **document revision tracking**, **change tracking**, and **OOXML** revision markup (insertions `<w:ins>` and deletions `<w:del>`) so you can programmatically accept text, list revisions with author and date, and apply insertions, deletions, or replacements with full revision metadata.

Use it for **Microsoft Word**-compatible revision tracking: parse DOCX files with track changes on, get accepted (clean) text, enumerate revisions per paragraph, or write new revisions (insert/delete/replace) that show up as track changes in Word.
