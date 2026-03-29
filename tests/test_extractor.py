import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from upwork_extractor import UpworkExtractor
from upwork_extractor import cli


def make_saved_page(
    description: str,
    title: str = "Test Job",
    attachments: list[dict[str, object]] | None = None,
) -> str:
    attachments = attachments or []
    payload: list[object] = [
        ["Reactive", 1],
        {"vuex": 2},
        {"jobDetails": 3},
        {"job": 4},
        {
            "uid": 5,
            "title": 6,
            "description": 7,
            "attachments": 8,
        },
        "123456",
        title,
        description,
        [],
    ]

    attachment_indexes = []
    for attachment in attachments:
        file_name_index = len(payload)
        payload.append(attachment["fileName"])

        uri_index = len(payload)
        payload.append(attachment["uri"])

        attachment_index = len(payload)
        payload.append(
            {
                "fileName": file_name_index,
                "uri": uri_index,
            }
        )
        attachment_indexes.append(attachment_index)

    payload[8] = attachment_indexes
    raw_json = json.dumps(payload)
    return f'<html><body><script type="application/json">{raw_json}</script></body></html>'


def test_extracts_title_and_markdown_body():
    html = make_saved_page(
        "<p>Hello <strong>world</strong>.</p><ul><li>One</li><li>Two</li></ul>"
    )

    job = UpworkExtractor.from_string(html).extract()

    assert job.title == "Test Job"
    assert job.to_markdown() == "# Test Job\n\nHello **world**.\n\n- One\n- Two\n"


def test_preserves_plain_text_descriptions():
    html = make_saved_page("First paragraph.\n\nSecond paragraph.")

    job = UpworkExtractor.from_string(html).extract()

    assert job.to_markdown() == "# Test Job\n\nFirst paragraph.\n\nSecond paragraph.\n"


def test_renders_links_and_ordered_lists():
    html = make_saved_page(
        "<p>Read <a href=\"https://example.com\">this brief</a>.</p>"
        "<ol><li>First</li><li>Second</li></ol>"
    )

    job = UpworkExtractor.from_string(html).extract()

    assert "[this brief](https://example.com)" in job.to_markdown()
    assert "1. First" in job.to_markdown()
    assert "2. Second" in job.to_markdown()


def test_renders_attachments_as_markdown_links():
    html = make_saved_page(
        "<p>Converted</p>",
        attachments=[
            {
                "fileName": "brief.pdf",
                "uri": "/att/download/openings/123/attachments/abc/download",
            },
            {
                "fileName": "screenshot.png",
                "uri": "/att/download/openings/123/attachments/def/download",
            },
        ],
    )

    job = UpworkExtractor.from_string(html).extract()

    assert "## Attachments" in job.to_markdown()
    assert "- [brief.pdf](https://www.upwork.com/att/download/openings/123/attachments/abc/download)" in job.to_markdown()
    assert "- [screenshot.png](https://www.upwork.com/att/download/openings/123/attachments/def/download)" in job.to_markdown()


def test_cli_writes_markdown_file(capsys, tmp_path: Path):
    saved_page = tmp_path / "posting.html"
    saved_page.write_text(make_saved_page("<p>Converted</p>"), encoding="utf-8")

    exit_code = cli.main([str(saved_page)])
    captured = capsys.readouterr()
    output_file = tmp_path / "posting.md"

    assert exit_code == 0
    assert output_file.read_text(encoding="utf-8") == "# Test Job\n\nConverted\n"
    assert output_file.exists()
    assert captured.out == ""
    assert captured.err == ""


def test_wrong_file_error():
    with pytest.raises(ValueError, match="expected Upwork job data"):
        UpworkExtractor.from_string("<html><body>no payload here</body></html>").extract()


def test_cli_fails_when_input_does_not_contain_html(capsys, tmp_path: Path):
    saved_page = tmp_path / "posting.txt"
    saved_page.write_text("plain text only", encoding="utf-8")

    exit_code = cli.main([str(saved_page)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "Error: Input file does not contain HTML.\n"
    assert not (tmp_path / "posting.md").exists()
