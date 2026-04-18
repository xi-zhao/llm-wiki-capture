# llm-wiki-capture

An OpenClaw skill for capturing noteworthy links and short notes into LLM-Wiki-Cli (FOKB) for long-term recall.

## What it does

- ingest WeChat and normal web URLs through FOKB
- turn short free-form notes into staged local HTML pages, then ingest them through `file://` URLs
- return structured JSON so an agent can confirm what was captured

## Files

- `SKILL.md`: the skill definition
- `scripts/capture_to_fokb.py`: helper CLI used by the skill
- `dist/llm-wiki-capture.skill`: packaged skill artifact

## Requirements

- Python 3
- a working `LLM-Wiki-Cli` / `fokb` checkout

The helper script looks for FOKB in this order:

1. `--fokb-base`
2. `FOKB_BASE`
3. current working directory, if it looks like `LLM-Wiki-Cli`
4. `~/LLM-Wiki-Cli`
5. `~/.openclaw.pre-migration/releases/LLM-Wiki-Cli`
6. `~/.openclaw/releases/LLM-Wiki-Cli`

## Usage

Capture a URL:

```bash
python3 scripts/capture_to_fokb.py --url "https://example.com"
```

Capture a short note:

```bash
python3 scripts/capture_to_fokb.py \
  --title "An idea worth keeping" \
  --text "This is the note content"
```

Capture from stdin:

```bash
echo "A small note worth saving" | python3 scripts/capture_to_fokb.py --stdin --title "Quick note"
```

## Notes

This repo contains only the reusable skill and helper CLI. It does not include a full LLM-Wiki-Cli checkout.
