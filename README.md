# upwork-extractor 🦷

Extracts structured job data from saved Upwork job posting HTML files, generating Markdown, YAML, or JSON.

## Use Case

Meant to work with the HTML content of job postings opened in their own window, the URL having the form `https://www.upwork.com/jobs/<slug>`. Useful for agentic CV optimization based on the CAPTCHA-protected job posting content or for Obsidian notes.

## Installation

```bash
uv tool install path/to/this-project-directory # or
uv tool install --editable path/to/this-project-directory # reflects code changes when run
```

If `upwork-extract` is not found after installation:

```bash
uv tool update-shell
```

## Local fixture for tests

To run the tests, save the HTML of a real Upwork job posting to `tests/fixtures/sample.html`

## Usage

```bash
upwork-extract posting.html > job-posting.md
upwork-extract posting.html --format json > job-posting.json
upwork-extract posting.html --format yaml > job-posting.yaml
```

## Running tests

```bash
uv run pytest tests/
```
