# llm-wiki-capture

An OpenClaw skill and helper CLI for capturing noteworthy links and short notes into LLM-Wiki-Cli (FOKB) for long-term recall.

## What it does

- ingest WeChat and normal web URLs through FOKB
- turn short free-form notes into staged local HTML pages, then ingest them through `file://` URLs
- return structured JSON so an agent can confirm what was captured
- give OpenClaw a reusable skill trigger for requests like “记录这个”, “沉淀一下”, “收进知识库”, or “以后可能会用到”

## Repo contents

- `SKILL.md`: the skill definition
- `scripts/capture_to_fokb.py`: helper CLI used by the skill
- `dist/llm-wiki-capture.skill`: packaged skill artifact

## Requirements

- Python 3
- a working `LLM-Wiki-Cli` / `fokb` checkout
- OpenClaw, if you want the agent to load the skill automatically

The helper script looks for FOKB in this order:

1. `--fokb-base`
2. `FOKB_BASE`
3. current working directory, if it looks like `LLM-Wiki-Cli`
4. `~/LLM-Wiki-Cli`
5. `~/.openclaw.pre-migration/releases/LLM-Wiki-Cli`
6. `~/.openclaw/releases/LLM-Wiki-Cli`

## Install the skill in OpenClaw

OpenClaw loads custom skills from several locations, including:

- `<workspace>/skills` for workspace-local skills
- `~/.openclaw/skills` for machine-wide shared skills

### Option 1, clone into a workspace

```bash
git clone https://github.com/xi-zhao/llm-wiki-capture.git ~/.openclaw/workspace/skills/llm-wiki-capture
```

Then start a new session or restart the gateway:

```bash
openclaw gateway restart
```

Optionally verify it is visible:

```bash
openclaw skills list
```

### Option 2, install as a shared skill

```bash
git clone https://github.com/xi-zhao/llm-wiki-capture.git ~/.openclaw/skills/llm-wiki-capture
openclaw gateway restart
```

### Option 3, install from the packaged `.skill` release artifact

Download `llm-wiki-capture.skill` from the latest release, then unpack it into a skill directory:

```bash
mkdir -p ~/.openclaw/skills
unzip llm-wiki-capture.skill -d ~/.openclaw/skills
openclaw gateway restart
```

The archive expands to:

```text
~/.openclaw/skills/llm-wiki-capture/
  SKILL.md
  scripts/capture_to_fokb.py
```

## Use as a standalone helper CLI

You can use the helper even outside OpenClaw.

### Capture a URL

```bash
python3 scripts/capture_to_fokb.py --url "https://example.com"
```

### Capture a short note

```bash
python3 scripts/capture_to_fokb.py \
  --title "An idea worth keeping" \
  --text "This is the note content"
```

### Capture from stdin

```bash
echo "A small note worth saving" | python3 scripts/capture_to_fokb.py --stdin --title "Quick note"
```

### Pass an explicit FOKB path

```bash
python3 scripts/capture_to_fokb.py \
  --fokb-base ~/LLM-Wiki-Cli \
  --url "https://example.com"
```

Or set it once:

```bash
export FOKB_BASE=~/LLM-Wiki-Cli
```

## Example output

The helper prints one JSON object. Typical fields:

```json
{
  "ok": true,
  "input_kind": "url",
  "ingest_url": "https://example.com",
  "staging_file": null,
  "fokb_base": "/path/to/LLM-Wiki-Cli",
  "result": {
    "ok": true,
    "command": "ingest",
    "result": {
      "title": "Example title",
      "files": {
        "parsed": "/path/to/parsed.md",
        "brief": "/path/to/brief.md"
      }
    }
  }
}
```

## How the OpenClaw skill is meant to be used

The skill is designed for durable capture requests, not temporary reminders.

Good fits:
- interesting articles or links
- snippets worth reusing later
- quick research notes
- chat text that should become long-term knowledge

Not a great fit:
- trivial acknowledgements
- reminders or tasks better handled by a reminder system
- sensitive content that should not be written to disk without explicit confirmation

## Notes

This repo contains only the reusable skill and helper CLI. It does not include a full LLM-Wiki-Cli checkout.
