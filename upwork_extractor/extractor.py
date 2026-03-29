from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from markdownify import markdownify


_DEVALUE_SPECIAL_TAGS = frozenset({
    "Reactive", "Set", "Map", "Date", "RegExp", "Error",
    "URL", "BigInt", "undefined", "NaN", "Infinity", "-Infinity", "-0",
})

_WRONG_FILE_ERROR = """\
Could not find the expected Upwork job data in this HTML file.
"""

_NOT_HTML_ERROR = "Input file does not contain HTML."
_UPWORK_BASE_URL = "https://www.upwork.com"


def _revive_devalue(data: list[Any]) -> Any:
    cache: dict[int, Any] = {}

    def resolve(index: int) -> Any:
        if index in cache:
            return cache[index]

        item = data[index]

        if isinstance(item, dict):
            result: dict[str, Any] = {}
            cache[index] = result
            for key, value in item.items():
                result[key] = resolve(value)
            return result

        if isinstance(item, list):
            if item and isinstance(item[0], str) and item[0] in _DEVALUE_SPECIAL_TAGS:
                tag = item[0]
                if tag == "Reactive":
                    resolved = resolve(item[1])
                    cache[index] = resolved
                    return resolved
                if tag == "Date":
                    cache[index] = item[1]
                    return item[1]
                cache[index] = None
                return None

            result_list: list[Any] = []
            cache[index] = result_list
            for value in item:
                result_list.append(resolve(value))
            return result_list

        cache[index] = item
        return item

    header = data[0]
    root_index = header[1] if isinstance(header, list) and header[0] == "Reactive" else 1
    return resolve(root_index)


def _render_markdown(html: str) -> str:
    content = html.strip()
    if not content:
        return ""
    if "<" not in content or ">" not in content:
        return content
    markdown = markdownify(
        content,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
    )
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    return markdown.strip()


def _contains_html(content: str) -> bool:
    return bool(re.search(r"<[a-zA-Z][^>]*>", content))


@dataclass
class Attachment:
    file_name: str
    uri: str

    @property
    def url(self) -> str:
        return f"{_UPWORK_BASE_URL}{self.uri}"


@dataclass
class ExtractedJob:
    title: str
    description_html: str
    attachments: list[Attachment]

    def to_markdown(self) -> str:
        body = _render_markdown(self.description_html)
        attachments = self._render_attachments()
        if self.title and body:
            return f"# {self.title}\n\n{body}{attachments}"
        if self.title:
            return f"# {self.title}{attachments}"
        if body:
            return f"{body}{attachments}"
        return attachments.lstrip("\n") if attachments else ""

    def _render_attachments(self) -> str:
        if not self.attachments:
            return "\n"

        lines = ["", "", "## Attachments", ""]
        for attachment in self.attachments:
            lines.append(f"- [{attachment.file_name}]({attachment.url})")
        return "\n".join(lines) + "\n"


class UpworkExtractor:
    _PAYLOAD_RE = re.compile(
        r'<script[^>]+type=["\']application/json["\'][^>]*>(.*?)</script>',
        re.DOTALL,
    )

    def __init__(self, html: str):
        self._html = html
        self._state: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: str | Path) -> "UpworkExtractor":
        return cls(Path(path).read_text(encoding="utf-8"))

    @classmethod
    def from_string(cls, html: str) -> "UpworkExtractor":
        return cls(html)

    def _get_state(self) -> dict[str, Any]:
        if self._state is not None:
            return self._state

        if not _contains_html(self._html):
            raise ValueError(_NOT_HTML_ERROR)

        for raw_json in self._PAYLOAD_RE.findall(self._html):
            try:
                flat = json.loads(raw_json)
            except json.JSONDecodeError:
                continue

            if not isinstance(flat, list):
                continue

            try:
                root = _revive_devalue(flat)
                root["vuex"]["jobDetails"]["job"]["uid"]
            except (KeyError, TypeError, IndexError):
                continue

            self._state = root
            return self._state

        raise ValueError(_WRONG_FILE_ERROR)

    def extract(self) -> ExtractedJob:
        job = self._get_state()["vuex"]["jobDetails"]["job"]
        description_html = self._extract_description(job)
        return ExtractedJob(
            title=job.get("title", "").strip(),
            description_html=description_html,
            attachments=self._extract_attachments(job),
        )

    def _extract_description(self, job: dict[str, Any]) -> str:
        for field_name in ("descriptionHtml", "description", "legacyCiphertextDescription"):
            value = job.get(field_name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _extract_attachments(self, job: dict[str, Any]) -> list[Attachment]:
        attachments = job.get("attachments")
        if not isinstance(attachments, list):
            return []

        extracted_attachments = []
        for attachment in attachments:
            if not isinstance(attachment, dict):
                continue

            file_name = attachment.get("fileName")
            uri = attachment.get("uri")
            if not isinstance(file_name, str) or not file_name.strip():
                continue
            if not isinstance(uri, str) or not uri.startswith("/"):
                continue

            extracted_attachments.append(
                Attachment(
                    file_name=file_name.strip(),
                    uri=uri,
                )
            )

        return extracted_attachments
