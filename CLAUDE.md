# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**vocabmorizer** — a tool to help remember and practise vocabulary and phrases for second language acquisition.

This is a Python project (inferred from the `.gitignore`). No build system, dependencies, or source code have been added yet.

## Setup & Commands

Add commands here as the project takes shape. Likely candidates based on the Python tooling in `.gitignore`:

```bash
# Install dependencies (update once a package manager is chosen)
uv sync          # if using uv
pip install -e . # if using pip + pyproject.toml

# Run tests
pytest

# Lint / format
ruff check .
ruff format .
```

## Architecture

To be documented once the codebase is established. The project's purpose — vocabulary/phrase practice for second-language learners — suggests:

- A data layer for storing vocabulary entries and progress
- A review/quiz engine (spaced repetition or similar)
- A user-facing interface (CLI, web app, or both)
