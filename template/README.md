# Council — Phase 1 Template

> Artifact governance for AI coding agents. Part of the [chief-tribe](https://github.com/thaitype/chief-tribe) ecosystem.

## What is this?

Council governs what happens to an agent's work. Instead of letting agents execute commands directly, agents produce **artifacts** (scripts) that humans review and execute.

```
Agent produces script → Human reviews → Human executes
```

## Quick Start

1. Copy this template into your project:

```bash
cp -r template/ your-project/
```

2. Your project now has:

```
your-project/
├── AGENTS.md                          # Agent rules
├── .agents/skills/                    # Council skills
│   ├── council-create/                # Agent submits work
│   ├── council-list/                  # Query artifacts
│   ├── council-review/                # Human approves/rejects
│   └── council-execute/               # Human runs approved work
└── .council/
    ├── scripts/council_lib.py         # Shared library
    ├── artifacts/                     # Agent writes scripts here
    └── data/artifacts.jsonl           # Event log
```

3. The agent reads `AGENTS.md`, learns the rules, and uses `council-create` to submit work.

## Workflow

### Agent creates an artifact

```bash
mkdir -p .council/artifacts/fix-nginx
# Agent writes fix-nginx/restart.sh
python .agents/skills/council-create/scripts/council-create.py \
  --id fix-nginx --type remediation --risk low \
  --summary "Restart nginx after config update" \
  --script .council/artifacts/ART-001-fix-nginx/restart.sh
```

### Human reviews

```bash
# List pending artifacts
python .agents/skills/council-list/scripts/council-list.py --status created

# Read the script, then approve or reject
python .agents/skills/council-review/scripts/council-review.py ART-001-fix-nginx --approve --comment "looks good"
```

### Human executes

```bash
python .agents/skills/council-execute/scripts/council-execute.py ART-001-fix-nginx
```

## Requirements

- Python 3.10+
- No external dependencies

## License

MIT
