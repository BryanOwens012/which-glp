# WhichGLP Development Guide - AGENTS.md

## Project Overview

**Project Name:** WhichGLP
**Domain:** whichglp.com
**Purpose:** Aggregation and analysis platform for weight-loss drug (GLP-1 agonist) reviews and real-world outcomes
**Data Sources:** Reddit posts/comments (Reddit API), Twitter posts (Twitter API via twitterapi.io), user-submitted reviews (future)
**Target Users:** General public researching weight-loss medications (non-technical, unfamiliar with drugs/biotech/medical terminology)

### Mission Statement
WhichGLP creates the definitive real-world dataset for GLP-1 weight-loss drug outcomes by aggregating thousands of anonymous user experiences from social media, structuring unstructured text data, and providing personalized predictions that generic LLMs cannot generate.

---

## Documentation Structure

This project uses multiple documentation files for organization:

- **AGENTS.md** (this file) - Development process, coding standards, workflow
- **CLAUDE.md** - Technical development guide for Claude Code AI assistant
- **TECH_SPEC.md** - Technical specifications: drugs, data sources, tech stack, pipelines
- **MONETIZATION.md** (private, not committed) - Business strategy, revenue models, market analysis

For technical details about drugs, subreddits, tech stack, and data pipelines, see **TECH_SPEC.md**.

For business strategy, competitive analysis, and revenue projections, see **MONETIZATION.md** (keep local, do not commit).

---

## Root of this Monorepo

This monorepo is rooted at this file's enclosing directory. That is, this file is `./AGENTS.md` (inside repository root).

All git operations are to be run from this root directory.

If you work with Python files, preemptively ensure that you've activated the venv, which is typically at `./venv` (inside this root directory). If the venv does not exist, create it.

All Python dependencies are to be installed from this root directory (with its venv activated), and all dependencies are to be listed in requirements.txt in this root directory via `$ pip3 freeze > requirements.txt`.

---

## Development Process

- Always consult the documentation, which you can fetch and follow, to make sure you understand how to use the libraries and tools available.
- If in doubt, conduct web searches to find additional relevant information. Fetch documentation and review it to ensure you understand how to use libraries and tools correctly.
- Work in this repo/directory (and its subdirectories) only. Never touch any files outside this repo/directory/subdirectories unless explicitly instructed to do so.
- It is your responsibility to manage the environment (using 'uv' if Python), prepare it for working, updating dependencies, and installing any new dependencies you may need. E.g., whenever you need to install a new Python package, you should install it in the virtual environment using pip (`$ pip3 install --upgrade <package_name>`) and then update the requirements.txt file accordingly using `$ pip3 freeze > requirements.txt`.
- Always test your changes before moving on to the next checkpoint/milestone. Make sure everything works as expected.

---

## Coding Standards

### Style

- If Python code, then use Python 3 and follow PEP8 style guidelines.
- Prioritise readability - make code easy to read and understand by using small functions, avoiding unnecessary complexity (including sophisticated safety mechanisms, typing, complex patterns, etc. ... when they are not strictly necessary).
- Add type hints whenever possible. Make sure the type hints are correct; watch out especially for complex types (e.g., lists of dictionaries, optional types, etc.).
- Use linters/formatters (e.g., black, flake8 for Python; eslint, prettier for JavaScript/TypeScript) to ensure consistent code style.
- Write unit tests and integration tests for critical functions and components. Use testing frameworks like pytest (Python), or Jest or React Testing Library (JavaScript/TypeScript).
- Follow best practices for error handling and logging. Use try-except blocks in Python, and proper error handling in JavaScript/TypeScript (e.g., Promises with .catch). Use descriptive error messages and error class names.
- Use consistent naming conventions for variables, functions, classes, and modules. Prefer descriptive names over abbreviations.
- Write modular code - break down large functions into smaller, reusable functions.
- Concise but clear explanatory comments to all code paths. The code you generated is being read by humans to learn and understand how the program works, so make it easy for them to follow. Add comments to every function, every if and else block, everywhere where commentary can help the reader understand how the code works.
- Always prefer clarity over brevity.
- Use docstrings, multiline comments, etc. (as the convention may be with the particular framework/library/language) to document all functions, classes, and modules. Include descriptions of parameters, return values, and any exceptions raised.
- Include links to any online docs or references you used to learn how to use a library, tool, or API, if applicable.
- Remove any unused imports, variables, functions, or code blocks.
- Avoid hardcoding values; use constants or configuration files instead.

---

## Living Documentation (the file ./AGENTS_APPENDLOG.md)

- That document (AGENTS_APPENDLOG.md) serves as the secondary instruction for you, after this primary AGENTS.md.
- Append to that document only. Do not remove or modify existing content, even if it is incorrect or outdated. That document is meant to be an append-only log.
- Keep notes there about your development process, decisions made, the current architecture of the project.
- Whenever you make code changes, remember to append your proposed changes to that file (append-only; don't delete its existing content), and then append to that file again to state that you've completed the changes when you've completed the changes
- That document is very long and won't fit into your context window. No worries: you don't have to read all of it. Please just, say, read the last 100 lines of it to know generally what's in it, and then append, since it's an append-only doc.
