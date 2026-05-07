# Docshelf

A lightweight self-hosted markdown viewer. Drop `.md` files into a folder and browse them as clean, readable pages on your local network.

Created through a Claude Code test session. 

Built with Django and runs in Docker.

## Features

- Renders markdown files from a local `docs/` directory
- Clean, readable layout with syntax-highlighted code blocks
- No database, no accounts, no configuration files — just files
- Serves over your local network out of the box

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

```bash
pip install -r requirements.txt
DJANGO_SECRET_KEY=test-key python -m django test markdown_viewer.tests --settings=config.settings
```
