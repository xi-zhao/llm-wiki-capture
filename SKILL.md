---
name: llm-wiki-capture
description: Capture noteworthy URLs, WeChat articles, web pages, and short free-form notes into LLM-Wiki-Cli (fokb) for long-term recall. Use when the user asks to record, save, archive, collect,沉淀, 记一下, 收进知识库, or keep something for later, especially links, articles, or concise notes worth retrieving again.
---

# LLM Wiki Capture

Use LLM-Wiki-Cli as the default sink for content that is worth keeping beyond the current chat.

## Quick start

Read and run the bundled helper script relative to the skill directory.

Prefer:

```bash
python3 scripts/capture_to_fokb.py --url "https://example.com"
```

For free-form notes:

```bash
python3 scripts/capture_to_fokb.py \
  --title "一个值得记住的想法" \
  --text "这里是要沉淀的内容"
```

The helper handles two cases:
- URL input: call `fokb ingest <url>`
- Note input: stage a local HTML page, then ingest its `file://` URL into FOKB

## Decide when to use this skill

Use this skill when the user wants durable capture, not just a transient answer.

Common triggers:
- “记录这个”
- “这个挺有意思的，留一下”
- “帮我沉淀一下”
- “收进知识库”
- “以后可能会用到”

Good fits:
- WeChat article links
- normal web links
- short research snippets
- plain-text notes from chat that deserve long-term storage

Do not use this skill for:
- trivial acknowledgements
- reminders that belong in a task/reminder system
- sensitive content that should not be written to disk without confirmation

## Workflow

1. Identify the material worth keeping.
2. If the user supplied a URL, ingest the URL directly.
3. If the user supplied only text, pass the text through the helper script so it becomes a staged local page and then gets ingested.
4. Read the JSON result and confirm what was captured.
5. If the ingest fails, tell the user what blocked it and fall back to `memory/YYYY-MM-DD.md` only if the user still wants a local record.

## Commands

Direct ingest through FOKB:

```bash
python3 "$FOKB_BASE/scripts/fokb.py" ingest "https://example.com"
```

Optional digest generation:

```bash
python3 scripts/capture_to_fokb.py --url "https://example.com" --with-digests
```

Free-form note capture from stdin:

```bash
echo "这里是临时想到但值得留下的内容" | \
python3 scripts/capture_to_fokb.py --stdin --title "随手笔记"
```

## Output handling

The helper prints one JSON object with:
- `input_kind`: `url` or `note`
- `ingest_url`: final URL sent to FOKB
- `staging_file`: local staged file for note captures
- `result`: parsed FOKB ingest payload

Prefer reporting back these fields when relevant:
- captured title
- source URL
- parsed/brief file paths if the user wants traceability
- whether digests were generated

## Environment assumptions

The helper script tries to find FOKB in this order:
- `--fokb-base`
- `FOKB_BASE`
- current working directory if it looks like `LLM-Wiki-Cli`
- `~/LLM-Wiki-Cli`
- `~/.openclaw.pre-migration/releases/LLM-Wiki-Cli`
- `~/.openclaw/releases/LLM-Wiki-Cli`

Staged note pages default to a temporary directory.

If auto-discovery fails, pass:
- `--fokb-base`
- `--staging-dir`

## Guardrails

Keep captures concise and intentional.

Before writing, pause if:
- the content is private and the user did not clearly ask to store it
- the content is a duplicate of something just ingested
- the user asked for temporary memory only, not durable knowledge capture
