---
title: Docshelf
author: harley@davisdiscovers.dev
tags: [readme, docshelf]
---
# Docshelf

A lightweight self-hosted markdown viewer. Drop `.md` files into a folder and browse them as clean, readable pages on your local network.

Created through a Claude Code test session. 

Built with Django and runs in Docker.

## Features

- Renders markdown files from a local `docs/` directory
- Clean, readable layout with syntax-highlighted code blocks
- Command palette search — press `⌘K` / `Ctrl+K` to jump to any document
- Tag-based filtering on the document index
- Auto-generated table of contents in each document view
- No database, no accounts, no configuration files — just files
- Serves over your local network out of the box

## Requirements

- Python 3.12 (see `.python-version`)
- Docker + Docker Compose (recommended for running the app)

## Getting started

**1. Clone the repo**

```bash
git clone https://github.com/harleyndavis/docshelf.git
cd docshelf
```

**2. Set your secret key**

```bash
cp .env.example .env
# Edit .env and set a value for DJANGO_SECRET_KEY
```

**3. Add your docs**

Drop any `.md` files into the `docs/` directory. Subdirectory nesting is not currently supported — files must be at the top level of `docs/`.

**4. Start the server**

```bash
docker compose up -d
```

The app will be available at `http://localhost:8000`. On your local network, replace `localhost` with your machine's IP address.

## Configuration

All configuration is via environment variables, set in your `.env` file:

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | — | **Required.** A long random string. |
| `DJANGO_DEBUG` | `false` | Set to `true` to enable debug mode. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated list of allowed hostnames/IPs. Add your local IP to access from other devices. |
| `GUNICORN_WORKERS` | `2` | Number of worker processes. |

**Example `.env` for local network access:**

```env
DJANGO_SECRET_KEY=your-long-random-secret-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.50
```

## Generating a secret key

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Running tests

From the project root, with the virtual environment active:

```bash
pip install -r requirements.txt
.venv/bin/python.exe -m django test markdown_viewer.tests --settings=config.settings
```

On Windows (PowerShell):

```powershell
pip install -r requirements.txt
.venv\Scripts\python.exe -m django test markdown_viewer.tests --settings=config.settings
```

The `DJANGO_SECRET_KEY` environment variable must be set before running tests. The test module sets a default automatically, so any non-empty value works:

```bash
DJANGO_SECRET_KEY=test-key .venv/bin/python.exe -m django test markdown_viewer.tests --settings=config.settings
```

## Document metadata

Documents can include optional YAML frontmatter to control how they appear in the index and document views.

```markdown
---
title: My Document
category: Notes
summary: A short description shown in the document list.
updated: 2026-05-07
read_time: 3
tags: [notes, howto, reference]
---

# Content starts here
```

All fields are optional. The table below describes each supported field:

| Field | Type | Where it appears | Falls back to |
|---|---|---|---|
| `title` | string | Document heading, index list, sidebar, browser tab | Prettified filename slug |
| `category` | string | Eyebrow label above the document title | — |
| `summary` | string | Subtitle row in the document index | — |
| `updated` | date (`YYYY-MM-DD`) | Index list and document footer | File modification date |
| `read_time` | integer (minutes) | Index list and document header | Calculated from word count (÷ 275, minimum 1 min) |
| `tags` | list | Filter bar on the index; included in search | — |

Tags can be written as a YAML list or a comma-separated string:

```yaml
tags: [notes, howto, reference]   # list form
tags: notes, howto, reference     # string form — both are equivalent
```

Without frontmatter the filename slug is used as the title and no metadata is shown.

## Notes

**Live-mounted volume:** Only the `docs/` directory is mounted as a Docker volume. Changes to templates, views, settings, or any other source file require rebuilding the image (`docker compose up -d --build`).

**Raw HTML in markdown is disabled:** The renderer strips raw HTML blocks and inline HTML from `.md` files. This prevents XSS from untrusted documents.

**Filename slugs:** Document filenames must consist only of letters, numbers, hyphens, and underscores (`[-a-zA-Z0-9_]`) to be accessible via the URL. Files with other characters in their names will not be reachable.
