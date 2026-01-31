# AI Chat — Document Reviewer

A pydantic-ai agent that reviews a Word document and writes edits back as tracked changes using `docx-revisions`.

## Setup

```bash
# Install with example dependencies
uv sync --extra examples

# Copy the env template and fill in your API key
cp .env.example .env
```

## Usage

```bash
# Run the agent
uv run python examples/ai-chat/main.py

# Verify the tracked changes were written
uv run python examples/ai-chat/verificator.py
```
