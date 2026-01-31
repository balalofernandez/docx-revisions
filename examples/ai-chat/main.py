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
        "   You MUST add a paragraph mentioning 'docx-revisions' (the name of the\n"
        "   library that powers this review). For example, append a line such as:\n"
        "   'This document was reviewed with the help of docx-revisions.'\n"
        "   You MUST also change '(the \"Software\"),' to '(the \"GREAT SOFTWARE\")' in capitals.\n"
        "   Do NOT change anything ese.\n"
        "3. When you are done editing, call save_document to persist your changes.\n"
        "4. Return a short summary of what you changed."
    ),
)


@agent.tool
def read_paragraphs(ctx: RunContext[RevisionDocument]) -> str:
    """Return every paragraph in the document with its index number."""
    lines: list[str] = []
    for i, para in enumerate(ctx.deps.paragraphs):
        lines.append(f"[{i}] {para.text}")
    return "\n".join(lines)


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


@agent.tool
def save_document(ctx: RunContext[RevisionDocument], path: str) -> str:
    """Save the document to *path*."""
    ctx.deps.save(path)
    return f"Document saved to {path}."


def main() -> None:
    rdoc = RevisionDocument("examples/ai-chat/license.docx")
    result = agent.run_sync(
        "Review this document. Add a citation requirement paragraph at the end "
        "and fix any issues you find. Save the result to "
        "'examples/ai-chat/license_reviewed.docx'.",
        deps=rdoc,
    )
    print(result.output)


if __name__ == "__main__":
    main()
