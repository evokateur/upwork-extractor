.PHONY: install uninstall test

install:
	uv tool install --editable .

uninstall:
	uv tool uninstall post-extractor

test:
	uv run pytest
