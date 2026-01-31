"""Verify that the AI reviewer added 'docx-revisions' as a tracked change."""

import sys

from docx_revisions import RevisionDocument


def main() -> None:
    path = "examples/ai-chat/license_reviewed.docx"
    rdoc = RevisionDocument(path)

    found = False
    for para in rdoc.paragraphs:
        for ins in para.insertions:
            if "docx-revisions" in ins.text:
                print("PASS: Found 'docx-revisions' in tracked insertion.")
                print(f"  Author : {ins.author}")
                print(f"  Text   : {ins.text!r}")
                found = True

    if not found:
        print("FAIL: No tracked insertion containing 'docx-revisions' was found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
