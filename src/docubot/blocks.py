"""HTML comment block replacement in markdown files."""

from __future__ import annotations

import re

BLOCK_RE = re.compile(
    r"<!--\s*docubot:(?P<name>[\w-]+)\s*-->\s*"
    r"(?P<content>.*?)"
    r"<!--\s*/docubot:\1\s*-->",
    re.DOTALL,
)


def replace_block(text: str, name: str, new_content: str) -> str:
    """Replace or append a docubot-managed block."""
    wrapped = f"<!-- docubot:{name} -->\n{new_content.strip()}\n<!-- /docubot:{name} -->"

    def replacer(m: re.Match[str]) -> str:
        if m.group("name") == name:
            return wrapped
        return m.group(0)

    if f"docubot:{name}" in text:
        return BLOCK_RE.sub(replacer, text)

    return text.rstrip() + "\n\n" + wrapped + "\n"


def get_block(text: str, name: str) -> str | None:
    for m in BLOCK_RE.finditer(text):
        if m.group("name") == name:
            return m.group("content").strip()
    return None
