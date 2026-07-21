"""Readable Markdown rendering for guided task workspaces.

The application intentionally avoids adding a third-party Markdown runtime.
This renderer supports the guide syntax used by Career Accelerator and emits
QTextDocument-friendly HTML with high-contrast inline code, readable links,
and line-numbered fenced code blocks.
"""

from __future__ import annotations

from html import escape
import re


_DOCUMENT_CSS = """
body {
  color: #edf2ff;
  background-color: #0f1a2d;
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 14px;
  line-height: 1.48;
}
h1 { color: #ffffff; font-size: 24px; margin: 2px 0 12px 0; }
h2 { color: #f4efff; font-size: 19px; margin: 22px 0 9px 0; }
h3 { color: #ddd0ff; font-size: 16px; margin: 17px 0 7px 0; }
h4 { color: #cbbaf4; font-size: 14px; margin: 14px 0 6px 0; }
p { margin: 7px 0; }
ul, ol { margin: 7px 0 10px 22px; }
li { margin: 4px 0; }
a { color: #8fc7ff; text-decoration: underline; }
blockquote {
  color: #d9e3f7;
  background-color: #15243d;
  border-left: 4px solid #a26cf4;
  margin: 12px 0;
  padding: 9px 12px;
}
hr { border: 0; border-top: 1px solid #334764; margin: 18px 0; }
.inline-code {
  color: #fff3c4;
  background-color: #211b34;
  border: 1px solid #554477;
  font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 2px 5px;
}
.path-code {
  color: #d8f0ff;
  background-color: #15243d;
  border: 1px solid #41607f;
  font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;
  font-size: 13px;
  padding: 2px 5px;
}
.guide-table {
  border-collapse: collapse;
  margin: 10px 0 14px 0;
  width: 100%;
}
.guide-table th, .guide-table td {
  border: 1px solid #415474;
  padding: 7px 9px;
  vertical-align: top;
}
.guide-table th { background-color: #233252; color: #ffffff; }
.guide-table td { background-color: #15243d; }
.code-shell {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0 16px 0;
  background-color: #0d1220;
  border: 1px solid #4b3c70;
}
.code-title {
  color: #cdbdf7;
  background-color: #211a36;
  border-bottom: 1px solid #4b3c70;
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 11px;
  font-weight: 600;
  padding: 6px 10px;
  letter-spacing: 0.4px;
}
.code-gutter {
  color: #7386a8;
  background-color: #10192a;
  border-right: 1px solid #34425b;
  font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;
  font-size: 14px;
  padding: 10px 9px;
  text-align: right;
  vertical-align: top;
  width: 38px;
}
.code-content {
  color: #f2f5ff;
  background-color: #0d1220;
  font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;
  font-size: 14px;
  padding: 10px 12px;
  vertical-align: top;
  white-space: pre-wrap;
}
"""


_PATH_PATTERN = re.compile(
    r"^(?:[A-Za-z]:[\\/]|\.{0,2}[\\/]|[\w .-]+[\\/])|"
    r"(?:[\\/][\w .-]+){1,}|"
    r"\.(?:md|sql|csv|json|yaml|yml|py|ipynb|xlsx|pbix)$",
    re.IGNORECASE,
)
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_INLINE_CODE_PATTERN = re.compile(r"`([^`\n]+)`")
_BOLD_PATTERN = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_PATTERN = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_BARE_URL_PATTERN = re.compile(r"(?<![\"'=])(https?://[^\s<]+)")


def _inline(text: str) -> str:
    """Render the small inline subset used by task guides."""
    placeholders: dict[str, str] = {}

    def stash(value: str) -> str:
        token = f"\x00TOKEN{len(placeholders)}\x00"
        placeholders[token] = value
        return token

    def link_repl(match: re.Match[str]) -> str:
        label = escape(match.group(1))
        url = escape(match.group(2), quote=True)
        return stash(f'<a href="{url}">{label}</a>')

    text = _LINK_PATTERN.sub(link_repl, text)

    def code_repl(match: re.Match[str]) -> str:
        value = match.group(1)
        class_name = "path-code" if _PATH_PATTERN.search(value) else "inline-code"
        return stash(f'<span class="{class_name}">{escape(value)}</span>')

    text = _INLINE_CODE_PATTERN.sub(code_repl, text)
    text = escape(text)
    text = _BOLD_PATTERN.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_PATTERN.sub(r"<em>\1</em>", text)

    def bare_url_repl(match: re.Match[str]) -> str:
        url = match.group(1)
        trimmed = url.rstrip(".,;:!?)")
        suffix = url[len(trimmed):]
        href = escape(trimmed, quote=True)
        return f'<a href="{href}">{escape(trimmed)}</a>{escape(suffix)}'

    text = _BARE_URL_PATTERN.sub(bare_url_repl, text)
    for token, value in placeholders.items():
        text = text.replace(escape(token), value)
    return text


def _code_block(lines: list[str], language: str) -> str:
    safe_lines = lines or [""]
    numbers = "<br>".join(str(index) for index in range(1, len(safe_lines) + 1))
    code = "<br>".join(escape(line).replace(" ", "&nbsp;") or "&nbsp;" for line in safe_lines)
    label = escape((language or "code").strip().upper())
    return (
        '<table class="code-shell" cellspacing="0" cellpadding="0">'
        f'<tr><td class="code-title" colspan="2">{label}</td></tr>'
        f'<tr><td class="code-gutter">{numbers}</td>'
        f'<td class="code-content">{code}</td></tr></table>'
    )


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def render_markdown_html(markdown_text: str) -> str:
    """Convert guide Markdown into readable QTextBrowser-compatible HTML."""
    lines = str(markdown_text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{_inline(' '.join(part.strip() for part in paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if list_kind and list_items:
            items = "".join(f"<li>{_inline(item)}</li>" for item in list_items)
            output.append(f"<{list_kind}>{items}</{list_kind}>")
        list_kind = None
        list_items.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            language = stripped[3:].strip()
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                code_lines.append(lines[index])
                index += 1
            output.append(_code_block(code_lines, language))
            index += 1
            continue

        if (
            "|" in line
            and index + 1 < len(lines)
            and _is_table_separator(lines[index + 1])
        ):
            flush_paragraph()
            flush_list()
            headers = _split_table_row(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(_split_table_row(lines[index]))
                index += 1
            head_html = "".join(f"<th>{_inline(cell)}</th>" for cell in headers)
            row_html = "".join(
                "<tr>" + "".join(f"<td>{_inline(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            output.append(
                f'<table class="guide-table"><thead><tr>{head_html}</tr></thead>'
                f"<tbody>{row_html}</tbody></table>"
            )
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{_inline(heading.group(2))}</h{level}>")
            index += 1
            continue

        if re.fullmatch(r"(?:-{3,}|\*{3,}|_{3,})", stripped):
            flush_paragraph()
            flush_list()
            output.append("<hr>")
            index += 1
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            flush_paragraph()
            flush_list()
            quote_lines = [quote.group(1)]
            index += 1
            while index < len(lines):
                nested = re.match(r"^>\s?(.*)$", lines[index].strip())
                if not nested:
                    break
                quote_lines.append(nested.group(1))
                index += 1
            output.append(f"<blockquote>{_inline(' '.join(quote_lines))}</blockquote>")
            continue

        unordered = re.match(r"^[-+*]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if unordered or ordered:
            flush_paragraph()
            desired = "ul" if unordered else "ol"
            if list_kind and list_kind != desired:
                flush_list()
            list_kind = desired
            list_items.append((unordered or ordered).group(1))
            index += 1
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            index += 1
            continue

        if list_kind:
            flush_list()
        paragraph.append(stripped)
        index += 1

    flush_paragraph()
    flush_list()
    body = "\n".join(output)
    return f"<html><head><style>{_DOCUMENT_CSS}</style></head><body>{body}</body></html>"


def raw_markdown_stylesheet() -> str:
    """Return a legible monospace editor style for raw Markdown tabs."""
    return (
        "QTextEdit {"
        "font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;"
        "font-size: 14px;"
        "line-height: 1.35;"
        "padding: 10px;"
        "background-color: #0d1525;"
        "color: #eef3ff;"
        "border: 1px solid #334866;"
        "border-radius: 8px;"
        "selection-background-color: #6543a5;"
        "}"
    )


def path_field_stylesheet() -> str:
    """Return a high-contrast monospace style for path fields."""
    return (
        "QLineEdit {"
        "font-family: Consolas, 'Cascadia Mono', 'Courier New', monospace;"
        "font-size: 13px;"
        "padding: 7px 9px;"
        "background-color: #121f35;"
        "color: #d9f1ff;"
        "border: 1px solid #405f80;"
        "border-radius: 7px;"
        "}"
    )
