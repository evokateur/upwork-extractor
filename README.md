# post-extractor

Converts job posting HTML into Markdown. Works with HTML files or URLs.

## Use Case

Useful for LLM analysis and Obsidian notes.

### Specialized Extractors (so far)

- Upwork (HTML saved from browser after solving CAPTCHA)
- Welcome to the Jungle (URLs or downloaded HTML)

## Installation

```bash
cd post-extractor
make install
```

## Usage

```bash
extract-post posting.html # creates posting.md
extract-post posting.html output.md
```

## Running tests

```bash
make test
```
