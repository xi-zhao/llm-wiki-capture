#!/usr/bin/env python3

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

DEFAULT_STAGING_DIR = Path(tempfile.gettempdir()) / "llm-wiki-capture"
URL_RE = re.compile(r"^(https?://|file://)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a URL or free-form note into LLM-Wiki-Cli/FOKB"
    )
    parser.add_argument("content", nargs="*", help="URL or note text")
    parser.add_argument("--url", help="Direct URL to ingest")
    parser.add_argument("--text", help="Free-form note text to ingest")
    parser.add_argument("--title", help="Optional title for a free-form note")
    parser.add_argument("--stdin", action="store_true", help="Read note text from stdin")
    parser.add_argument("--source", help="Optional source label for generated note pages")
    parser.add_argument("--with-digests", action="store_true", help="Pass --with-digests to fokb ingest")
    parser.add_argument("--fokb-base", help="Path to the LLM-Wiki-Cli base directory. If omitted, the script tries common locations and FOKB_BASE.")
    parser.add_argument("--staging-dir", help="Directory for staged local note pages. Defaults to a temporary directory.")
    return parser.parse_args()


def is_url(value: str) -> bool:
    return bool(value and URL_RE.match(value.strip()))


def slugify(value: str, max_len: int = 48) -> str:
    text = re.sub(r"\s+", "-", value.strip().lower())
    text = re.sub(r"[^a-z0-9\-\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "note"


def derive_text(args: argparse.Namespace) -> tuple[str | None, str | None]:
    if args.url:
        return args.url.strip(), None

    if args.stdin:
        text = sys.stdin.read().strip()
        return None, text or None

    if args.text:
        return None, args.text.strip()

    if not args.content:
        return None, None

    joined = " ".join(args.content).strip()
    if is_url(joined):
        return joined, None
    return None, joined


def derive_title(title: str | None, text: str) -> str:
    if title and title.strip():
        return title.strip()
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned[:80]
    return f"Captured note {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def build_html(title: str, text: str, source: str | None) -> str:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
    blocks = "\n".join(f"<p>{html.escape(line)}</p>" for line in paragraphs)
    now = datetime.now().isoformat()
    source_line = f"<p><strong>Source:</strong> {html.escape(source)}</p>" if source else ""
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\">
  <title>{html.escape(title)}</title>
  <meta name=\"author\" content=\"OpenClaw Capture\">
  <meta name=\"publishdate\" content=\"{now}\">
  <meta name=\"description\" content=\"Captured note for long-term recall\">
</head>
<body>
  <article>
    <h1>{html.escape(title)}</h1>
    {source_line}
    <p><strong>Captured at:</strong> {html.escape(now)}</p>
    {blocks}
  </article>
</body>
</html>
"""


def stage_note(title: str, text: str, source: str | None, staging_dir: Path) -> tuple[Path, str]:
    staging_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = slugify(title)
    html_path = staging_dir / f"{stamp}-{slug}.html"
    html_path.write_text(build_html(title, text, source), encoding="utf-8")
    return html_path, html_path.resolve().as_uri()


def parse_payload(stdout: str) -> dict:
    stripped = stdout.strip()
    if stripped:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {}


def candidate_fokb_bases() -> list[Path]:
    candidates: list[Path] = []
    env_base = os.environ.get("FOKB_BASE")
    if env_base:
        candidates.append(Path(env_base).expanduser())
    candidates.extend(
        [
            Path.cwd(),
            Path.home() / "LLM-Wiki-Cli",
            Path.home() / ".openclaw.pre-migration" / "releases" / "LLM-Wiki-Cli",
            Path.home() / ".openclaw" / "releases" / "LLM-Wiki-Cli",
        ]
    )
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        resolved = candidate.expanduser().resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        unique.append(resolved)
    return unique


def resolve_fokb_base(explicit_base: str | None) -> Path:
    if explicit_base:
        base = Path(explicit_base).expanduser().resolve()
        if (base / "scripts" / "fokb.py").exists():
            return base
        raise FileNotFoundError(f"fokb.py not found at {base / 'scripts' / 'fokb.py'}")

    for base in candidate_fokb_bases():
        if (base / "scripts" / "fokb.py").exists():
            return base

    searched = "\n".join(f"- {path}" for path in candidate_fokb_bases())
    raise FileNotFoundError(
        "Could not find LLM-Wiki-Cli. Set FOKB_BASE or pass --fokb-base. Searched:\n"
        f"{searched}"
    )


def resolve_staging_dir(explicit_dir: str | None) -> Path:
    if explicit_dir:
        return Path(explicit_dir).expanduser().resolve()
    return DEFAULT_STAGING_DIR.resolve()


def run_ingest(fokb_base: Path, url: str, with_digests: bool) -> tuple[dict, str]:
    fokb = fokb_base / "scripts" / "fokb.py"
    if not fokb.exists():
        raise FileNotFoundError(f"fokb.py not found at {fokb}")
    cmd = [sys.executable, str(fokb), "ingest", url]
    if with_digests:
        cmd.append("--with-digests")
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(fokb_base))
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "fokb ingest failed").strip())
    return parse_payload(proc.stdout), proc.stdout


def main() -> int:
    args = parse_args()
    url, text = derive_text(args)
    if not url and not text:
        print("Provide a URL, --text, or --stdin content.", file=sys.stderr)
        return 2

    fokb_base = resolve_fokb_base(args.fokb_base)
    staging_dir = resolve_staging_dir(args.staging_dir)
    staged_file = None
    ingest_url = url
    title = None
    input_kind = "url"

    if text is not None:
        title = derive_title(args.title, text)
        staged_file, ingest_url = stage_note(title, text, args.source, staging_dir)
        input_kind = "note"

    payload, raw_stdout = run_ingest(fokb_base, ingest_url, args.with_digests)
    result = {
        "ok": True,
        "input_kind": input_kind,
        "requested_title": title,
        "ingest_url": ingest_url,
        "staging_file": str(staged_file) if staged_file else None,
        "fokb_base": str(fokb_base),
        "result": payload,
        "raw_stdout": raw_stdout.strip(),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
