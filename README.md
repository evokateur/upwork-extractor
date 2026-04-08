# posting-extractor

Converts job posting HTML into Markdown. Works with HTML files or URLs.

## Use Case

Useful for LLM analysis and Obsidian notes.

### Specialized Extractors (so far)

- Upwork (saved HTML to get around CAPTCHA)
- Welcome to the Jungle (URLs or `wget`-saved HTML)

## Installation

```bash
cd posting-extract
make install
```

## Usage

```bash
posting-extract posting.html # creates posting.md
posting-extract posting.html output.md
```

## Running tests

```bash
make test
```
