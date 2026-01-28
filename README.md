# docx-revisions

<p align="center">
  <a href="https://balalofernandez.github.io/docx-revisions" target="_blank"><img src="https://img.shields.io/badge/Docs-0066FF" alt="Documentation"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
  <a href="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml"><img src="https://github.com/balalofernandez/docx-revisions/actions/workflows/docs.yml/badge.svg" alt="Docs"></a>
  <a href="https://pypi.org/project/docx-revisions" target="_blank"><img src="https://img.shields.io/pypi/v/docx-revisions" alt="PyPI"></a>
  <!-- <a href="https://pepy.tech/projects/docx-revisions"><img src="https://static.pepy.tech/badge/docx-revisions" alt="PyPI Downloads"></a> -->
</p>

A Python library extending python-docx with track changes support for reading and writing Word document revisions (`<w:ins>` and `<w:del>` elements). Provides clean APIs like `get_accepted_text()`, `get_revisions()`, `insert_with_tracking()`, `delete_with_tracking()`, and `replace_with_tracking()` for programmatic revision management.
