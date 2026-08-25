#!/usr/bin/env python3
"""Upload a local Markdown file to Lark Docs.

By default this creates a new document. Pass --doc to overwrite an existing
one (full replace: comments and extra blocks on that doc may be lost).
After a successful upload, the local Markdown file gets YAML frontmatter
with `metadata.lark_url` / `metadata.lark_doc_id`. That block is stripped
before upload so it does not appear in Lark. A later run without --doc reuses
`metadata.lark_url`.

Lark folder trees are not created here. Hierarchy lives in Drive / Wiki;
pass an existing parent with --parent-token or --parent-position if needed
(create only).

Local images are rewritten to Lark's @./ / <img path> form so
`lark-cli docs +create` / `+update --command overwrite` uploads them in
place. The CLI reads --content from @file (cwd-relative), so this script
stages a temp workspace and runs the command from there.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})")
IMAGE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\(\s*"
    r"(?:<(?P<angle>[^>]+)>|(?P<url>[^)\s]+))"
    r"(?P<title>\s+(?:\"[^\"]*\"|'[^']*'))?"
    r"\s*\)"
)
HTML_IMG = re.compile(r"<img\b([^>]*?)\s*/?>", re.IGNORECASE)
HTML_ATTR = re.compile(
    r'([^\s=]+)\s*=\s*("([^"]*)"|\'([^\']*)\'|([^\s>]+))',
    re.IGNORECASE,
)
REMOTE_PREFIXES = ("http://", "https://", "mailto:", "data:", "ftp://")
FRONTMATTER_OPEN = re.compile(r"^---[ \t]*\r?\n")
FRONTMATTER_CLOSE = re.compile(r"(?m)^---[ \t]*(?:\r?\n|$)")
FM_TOP_LEVEL_KEY_LINE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$")
FM_INDENTED_KEY_LINE = re.compile(r"^(\s+)([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$")
METADATA_KEY = "metadata"
LARK_URL_KEY = "lark_url"
LARK_DOC_ID_KEY = "lark_doc_id"


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(code)


def extract_parent_token(value: str) -> str:
    """Accept a raw token or a Drive/Wiki URL and return the token."""
    if not value.startswith(("http://", "https://")):
        return value
    path = urlparse(value).path.rstrip("/")
    token = path.split("/")[-1]
    if not token:
        die(f"could not extract token from URL: {value}")
    return token


def is_remote(url: str) -> bool:
    lowered = url.strip().lower()
    return lowered.startswith(REMOTE_PREFIXES)


def already_lark_local(url: str) -> bool:
    return url.startswith("@./") or url.startswith("@")


def split_fences(text: str) -> list[tuple[bool, str]]:
    """Split markdown into (is_code_fence, chunk) parts."""
    parts: list[tuple[bool, str]] = []
    buf: list[str] = []
    in_fence = False
    fence_marker = ""

    def flush(is_code: bool) -> None:
        if buf:
            parts.append((is_code, "".join(buf)))
            buf.clear()

    for line in text.splitlines(keepends=True):
        if in_fence:
            buf.append(line)
            stripped = line.lstrip()
            if stripped.startswith(fence_marker):
                rest = stripped[len(fence_marker) :].strip()
                if rest == "":
                    flush(True)
                    in_fence = False
                    fence_marker = ""
            continue

        m = FENCE_OPEN.match(line)
        if m:
            flush(False)
            in_fence = True
            fence_marker = m.group(2)[0] * len(m.group(2))
            buf.append(line)
            continue
        buf.append(line)

    flush(in_fence)
    return parts


def local_url_to_path(raw: str, md_dir: Path) -> Path | None:
    url = unquote(raw.strip())
    if is_remote(url) or url.startswith("#"):
        return None
    if already_lark_local(url):
        url = url[3:] if url.startswith("@./") else url[1:]
    url = url.split("?", 1)[0].split("#", 1)[0]
    url = url.replace("\\", "/")
    if not url:
        return None
    path = Path(url)
    return path if path.is_absolute() else (md_dir / path)


def parse_html_attrs(attr_text: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in HTML_ATTR.finditer(attr_text):
        name = match.group(1).lower()
        value = match.group(3)
        if value is None:
            value = match.group(4)
        if value is None:
            value = match.group(5) or ""
        attrs[name] = value
    return attrs


def xml_escape_text(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def xml_escape_attr(value: str) -> str:
    return xml_escape_text(value).replace('"', "&quot;")


def pixel_size(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if value.endswith("%"):
        return None
    if value.lower().endswith("px"):
        value = value[:-2].strip()
    return value if value.isdigit() else None


def rewrite_images(
    markdown: str,
    md_dir: Path,
    work_dir: Path,
) -> tuple[str, list[Path], list[str]]:
    """Rewrite local images to Lark @./ / <img path> form and copy them into work_dir.

    Supports Markdown `![alt](path)` and HTML `<img src="path">`.
    Missing local files are left unchanged so create can still succeed.
    """
    md_root = md_dir.resolve()
    copied: list[Path] = []
    missing: list[str] = []
    used_ext_names: set[str] = set()

    def dest_for(src: Path) -> Path:
        src = src.resolve()
        try:
            rel = src.relative_to(md_root)
            return work_dir / rel
        except ValueError:
            name = src.name
            stem = 1
            while name in used_ext_names:
                name = f"{src.stem}-{stem}{src.suffix}"
                stem += 1
            used_ext_names.add(name)
            return work_dir / "ext-assets" / name

    def stage_local(raw: str) -> str | None:
        """Return @./relative path after copying, or None if not a local file."""
        src = local_url_to_path(raw, md_dir)
        if src is None:
            return None
        if not src.is_file():
            missing.append(raw)
            return None
        dest = dest_for(src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists():
            shutil.copy2(src, dest)
            copied.append(dest)
        return f"@./{dest.relative_to(work_dir).as_posix()}"

    def rewrite_md_image(match: re.Match[str]) -> str:
        raw = (match.group("angle") or match.group("url") or "").strip()
        if is_remote(raw):
            return match.group(0)
        lark_path = stage_local(raw)
        if lark_path is None:
            return match.group(0)
        alt = match.group("alt")
        title = match.group("title") or ""
        if match.group("angle") is not None or " " in lark_path:
            return f"![{alt}](<{lark_path}>{title})"
        return f"![{alt}]({lark_path}{title})"

    def rewrite_html_image(match: re.Match[str]) -> str:
        attrs = parse_html_attrs(match.group(1))
        src = (attrs.get("src") or attrs.get("path") or attrs.get("href") or "").strip()
        if not src:
            return match.group(0)

        caption = attrs.get("caption") or attrs.get("alt") or attrs.get("title") or ""
        width = pixel_size(attrs.get("width"))
        height = pixel_size(attrs.get("height"))

        extra = ""
        if caption:
            extra += f' caption="{xml_escape_attr(caption)}"'
        if width:
            extra += f' width="{width}"'
        if height:
            extra += f' height="{height}"'

        if is_remote(src):
            return f'<img href="{xml_escape_attr(src)}"{extra}/>'

        lark_path = stage_local(src)
        if lark_path is None:
            return match.group(0)
        return f'<img path="{xml_escape_attr(lark_path)}"{extra}/>'

    def rewrite_chunk(chunk: str) -> str:
        chunk = HTML_IMG.sub(rewrite_html_image, chunk)
        return IMAGE.sub(rewrite_md_image, chunk)

    out: list[str] = []
    for is_code, chunk in split_fences(markdown):
        out.append(chunk if is_code else rewrite_chunk(chunk))
    return "".join(out), copied, missing


def strip_matching_h1(text: str, title: str) -> str:
    lines = text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i >= len(lines):
        return text
    m = re.match(r"^#\s+(.+?)\s*$", lines[i])
    if not m or m.group(1).strip() != title.strip():
        return text
    i += 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    body = "\n".join(lines[i:])
    if text.endswith("\n") and (not body.endswith("\n")):
        body += "\n"
    return body


def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    """Split leading YAML frontmatter. None inner lines means no frontmatter."""
    opened = FRONTMATTER_OPEN.match(text)
    if not opened:
        return None, text
    rest = text[opened.end() :]
    closed = FRONTMATTER_CLOSE.search(rest)
    if not closed:
        return None, text
    inner = rest[: closed.start()]
    body = rest[closed.end() :]
    return inner.splitlines(), body


def unquote_yaml_scalar(raw: str) -> str:
    value = raw.strip()
    if value and not (value.startswith(("'", '"')) and value.endswith(("'", '"'))):
        value = value.split(" #", 1)[0].rstrip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
        return parsed if isinstance(parsed, str) else value
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def metadata_bounds(lines: list[str]) -> tuple[int, int] | None:
    """Return the line range occupied by a block-style top-level metadata map."""
    for index, line in enumerate(lines):
        match = FM_TOP_LEVEL_KEY_LINE.match(line)
        if not match or match.group(1) != METADATA_KEY:
            continue
        raw_value = match.group(2).strip()
        if raw_value.startswith("#"):
            raw_value = ""
        else:
            raw_value = raw_value.split(" #", 1)[0].strip()
        if raw_value:
            return None
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if candidate and not candidate[0].isspace() and not candidate.startswith("#"):
                break
            end += 1
        return index, end
    return None


def metadata_child_indent(lines: list[str], start: int, end: int) -> str:
    indents = [
        match.group(1)
        for line in lines[start + 1 : end]
        if (match := FM_INDENTED_KEY_LINE.match(line))
    ]
    return min(indents, key=lambda indent: len(indent.expandtabs(8)), default="  ")


def frontmatter_value(lines: list[str], key: str) -> str | None:
    """Read a metadata child, accepting the old top-level form as a fallback."""
    bounds = metadata_bounds(lines)
    if bounds:
        start, end = bounds
        child_indent = metadata_child_indent(lines, start, end)
        for line in lines[start + 1 : end]:
            match = FM_INDENTED_KEY_LINE.match(line)
            if match and match.group(1) == child_indent and match.group(2) == key:
                return unquote_yaml_scalar(match.group(3))

    for line in lines:
        match = FM_TOP_LEVEL_KEY_LINE.match(line)
        if match and match.group(1) == key:
            return unquote_yaml_scalar(match.group(2))
    return None


def yaml_scalar(value: str) -> str:
    if value == "":
        return '""'
    if re.fullmatch(r"[A-Za-z0-9._/-]+", value):
        return value
    return json.dumps(value, ensure_ascii=False)


def set_metadata_key(lines: list[str], key: str, value: str) -> list[str]:
    """Set a direct child of the frontmatter metadata map, preserving other YAML."""
    bounds = metadata_bounds(lines)
    if bounds:
        start, end = bounds
        out = list(lines)
        child_indent = metadata_child_indent(lines, start, end)
        rendered = f"{child_indent}{key}: {yaml_scalar(value)}"
        for index in range(start + 1, end):
            match = FM_INDENTED_KEY_LINE.match(out[index])
            if match and match.group(1) == child_indent and match.group(2) == key:
                out[index] = rendered
                return out
        out.insert(end, rendered)
        return out

    if any(
        (match := FM_TOP_LEVEL_KEY_LINE.match(line))
        and match.group(1) == METADATA_KEY
        for line in lines
    ):
        die("frontmatter 'metadata' must be a block-style YAML mapping")

    out = list(lines)
    if out and out[-1].strip():
        out.append("")
    out.extend([f"{METADATA_KEY}:", f"  {key}: {yaml_scalar(value)}"])
    return out


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text[:4096] else "\n"


def render_with_frontmatter(fm_lines: list[str], body: str, newline: str = "\n") -> str:
    inner = newline.join(fm_lines)
    if fm_lines:
        inner += newline
    body = body.lstrip("\r\n")
    if body and not body.endswith(("\n", "\r")):
        body += newline
    return f"---{newline}{inner}---{newline}{newline}{body}"


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or overwrite a Lark Doc from a local Markdown file.",
        epilog=(
            "examples:\n"
            "  %(prog)s ./notes.md\n"
            "  %(prog)s ./notes.md --title 'Sprint notes'\n"
            "  %(prog)s ./notes.md --parent-token fldcnXXXX\n"
            "  %(prog)s ./notes.md --parent-token https://x.feishu.cn/wiki/wikcnXXXX\n"
            "  %(prog)s ./notes.md --parent-position my_library\n"
            "  %(prog)s ./notes.md --doc https://x.feishu.cn/docx/doxcnXXXX\n"
            "  %(prog)s ./notes.md --doc doxcnXXXX --title 'Sprint notes'\n"
            "  %(prog)s ./notes.md   # later runs reuse metadata.lark_url in YAML frontmatter\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("markdown_file", help="path to a local .md file")
    parser.add_argument(
        "legacy_prefix",
        nargs="?",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--title",
        help="document title (default: markdown filename without suffix)",
    )
    parser.add_argument(
        "--doc",
        help="existing document URL or token; overwrite that doc instead of creating a new one (overrides metadata.lark_url in frontmatter)",
    )
    parser.add_argument(
        "--parent-token",
        help="existing Drive folder token, Wiki node token, or URL (no folders are created)",
    )
    parser.add_argument(
        "--parent-position",
        help="parent position such as my_library; mutually exclusive with --parent-token",
    )
    parser.add_argument(
        "--as",
        dest="identity",
        choices=("user", "bot"),
        help="lark-cli identity (user or bot)",
    )
    parser.add_argument(
        "--keep-h1",
        action="store_true",
        help="keep a leading '# title' even when it matches --title",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail if any local image file is missing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="pass --dry-run to lark-cli (no document is created or updated)",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="keep the staging directory (prints its path)",
    )
    args = parser.parse_args(argv)

    if args.parent_token and args.parent_position:
        parser.error("--parent-token and --parent-position are mutually exclusive")
    if args.doc and (args.parent_token or args.parent_position):
        parser.error("--doc cannot be combined with --parent-token/--parent-position")
    if args.legacy_prefix:
        parser.error(
            "folder prefix is no longer supported; "
            "pass an existing Drive/Wiki parent with --parent-token or --parent-position"
        )
    return args


def run_cli(cmd: list[str], cwd: Path) -> dict:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        die("lark-cli not found in PATH")

    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0:
        if stdout:
            print(stdout, file=sys.stderr)
        if stderr:
            print(stderr, file=sys.stderr)
        die(f"lark-cli failed with exit code {proc.returncode}")

    if not stdout:
        if stderr:
            print(stderr, file=sys.stderr)
        die("lark-cli returned empty stdout")

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        print(stdout, file=sys.stderr)
        die("lark-cli stdout was not JSON")
    return payload


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    md_path = Path(args.markdown_file).expanduser()
    if not md_path.is_file():
        die(f"file not found: {md_path}")

    md_dir = md_path.parent.resolve()
    title = args.title or md_path.stem
    markdown = md_path.read_text(encoding="utf-8")
    if markdown.startswith("\ufeff"):
        markdown = markdown.lstrip("\ufeff")

    fm_lines, source_body = split_frontmatter(markdown)
    if fm_lines is None:
        fm_lines = []
        source_body = markdown
    if any(
        (match := FM_TOP_LEVEL_KEY_LINE.match(line))
        and match.group(1) == METADATA_KEY
        for line in fm_lines
    ) and metadata_bounds(fm_lines) is None:
        die("frontmatter 'metadata' must be a block-style YAML mapping")
    doc_ref = (
        args.doc
        or frontmatter_value(fm_lines, LARK_URL_KEY)
        or frontmatter_value(fm_lines, LARK_DOC_ID_KEY)
    )
    if doc_ref and (args.parent_token or args.parent_position):
        die(
            "--doc / metadata.lark_url cannot be combined with "
            "--parent-token/--parent-position"
        )

    work = Path(tempfile.mkdtemp(prefix="lark-doc-upload-"))
    try:
        rewritten, copied, missing = rewrite_images(source_body, md_dir, work)
        if not args.keep_h1:
            rewritten = strip_matching_h1(rewritten, title)

        # +update has no --title flag; prepend <title> so overwrite can rename.
        if doc_ref:
            rewritten = f"<title>{xml_escape_text(title)}</title>\n{rewritten}"

        body = work / "body.md"
        body.write_text(rewritten, encoding="utf-8")

        print(f"title: {title}", file=sys.stderr)
        print(f"images copied: {len(copied)}", file=sys.stderr)
        if doc_ref and not args.doc:
            print(f"reusing {METADATA_KEY}.{LARK_URL_KEY} from frontmatter", file=sys.stderr)
        if missing:
            print(f"missing local images ({len(missing)}):", file=sys.stderr)
            for ref in missing:
                print(f"  - {ref}", file=sys.stderr)
            if args.strict:
                die("missing local images (strict mode)")

        if doc_ref:
            cmd = [
                "lark-cli",
                "docs",
                "+update",
                "--command",
                "overwrite",
                "--doc",
                doc_ref,
                "--doc-format",
                "markdown",
                "--content",
                "@./body.md",
            ]
            action = "updating document via lark-cli docs +update --command overwrite ..."
        else:
            cmd = [
                "lark-cli",
                "docs",
                "+create",
                "--doc-format",
                "markdown",
                "--title",
                title,
                "--content",
                "@./body.md",
            ]
            if args.parent_token:
                cmd.extend(["--parent-token", extract_parent_token(args.parent_token)])
            if args.parent_position:
                cmd.extend(["--parent-position", args.parent_position])
            action = "creating document via lark-cli docs +create ..."
        if args.identity:
            cmd.extend(["--as", args.identity])
        if args.dry_run:
            cmd.append("--dry-run")

        print(action, file=sys.stderr)
        payload = run_cli(cmd, cwd=work)

        if args.dry_run:
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return 0

        if payload.get("ok") is False:
            json.dump(payload, sys.stderr, ensure_ascii=False, indent=2)
            sys.stderr.write("\n")
            die("lark-cli reported ok=false")

        data = payload.get("data") or {}
        document = data.get("document") or {}
        doc_id = (
            document.get("document_id")
            or data.get("document_id")
            or data.get("doc_id")
        )
        doc_url = document.get("url") or data.get("url") or data.get("doc_url")
        if not doc_url and doc_ref and str(doc_ref).startswith(("http://", "https://")):
            doc_url = doc_ref
        warnings = data.get("warnings") or []

        if warnings:
            print("warnings:", file=sys.stderr)
            for warning in warnings:
                print(f"  - {warning}", file=sys.stderr)

        notice = payload.get("_notice") or {}
        update = notice.get("update") if isinstance(notice, dict) else None
        if update:
            print(
                f"lark-cli update available: {update.get('message', update)}",
                file=sys.stderr,
            )

        if doc_url or doc_id:
            new_fm = list(fm_lines)
            if doc_url:
                new_fm = set_metadata_key(new_fm, LARK_URL_KEY, str(doc_url))
            if doc_id:
                new_fm = set_metadata_key(new_fm, LARK_DOC_ID_KEY, str(doc_id))
            write_text_atomic(
                md_path,
                render_with_frontmatter(new_fm, source_body, detect_newline(markdown)),
            )
            print(f"wrote YAML frontmatter to {md_path}", file=sys.stderr)
        else:
            print(
                "warning: upload succeeded but no document URL/id returned; "
                "frontmatter was not updated",
                file=sys.stderr,
            )

        print("Done. Document updated." if doc_ref else "Done. Document uploaded.")
        if doc_id:
            print(f"Document ID: {doc_id}")
        if doc_url:
            print(f"Document URL: {doc_url}")
        if not doc_id and not doc_url:
            json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        return 0
    finally:
        if args.keep_temp:
            print(f"temp workspace kept: {work}", file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
