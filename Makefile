.PHONY: install uninstall reinstall test

install:
	uv tool install --editable .

uninstall:
	uv tool uninstall post-extractor

reinstall:
	uv tool install --editable --reinstall .

test:
	uv run pytest
