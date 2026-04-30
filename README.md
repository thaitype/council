# Council

> Artifact governance for AI coding agents. Part of the [chief-tribe](https://github.com/thaitype/chief-tribe) ecosystem.

Agents produce scripts. Humans review and execute them. No direct execution.

```
Agent writes script → Human approves → Human executes
```

## Install

```bash
git clone https://github.com/thaitype/council.git
cp -r council/template/ your-project/
```

That's it. Your project now has:

```
your-project/
├── AGENTS.md                          # Agent governance rules
├── .agents/skills/                    # Council skills
│   ├── council-create/                # Agent submits artifacts
│   ├── council-list/                  # Query artifacts
│   ├── council-review/                # Human approves/rejects
│   └── council-execute/               # Human runs approved artifacts
└── .council/
    ├── scripts/council_lib.py         # Shared library
    ├── artifacts/                     # Agent writes scripts here
    └── data/artifacts.jsonl           # Event log
```

## Usage

### Agent creates an artifact

```bash
mkdir -p .council/artifacts/fix-nginx
# Agent writes the script
python .council/scripts/council-create.py \
  --id fix-nginx --type remediation --risk low \
  --summary "Restart nginx after config update" \
  --script .council/artifacts/ART-001-fix-nginx/restart.sh
```

### Human reviews

```bash
python .council/scripts/council-list.py --status created
python .council/scripts/council-review.py ART-001-fix-nginx --approve
```

### Human executes

```bash
python .council/scripts/council-execute.py ART-001-fix-nginx
```

## Requirements

- Python 3.10+
- No external dependencies

## How it works

- **AGENTS.md** tells the agent: don't run commands directly, submit artifacts instead
- **Skills** in `.agents/skills/` teach the agent the workflow
- **State** is event-sourced in `.council/data/artifacts.jsonl`
- **Scripts** live in `.council/artifacts/<id>/` as `.sh` or `.py` files

## Position in chief-tribe

```
chieftain  👑  Opinionated runtime + distribution
  chief    ⚔️  Portable framework + workflow structure
    sage   🧙  Baseline behavior principles
  council  🏛️  Artifact governance
```

Council governs what happens to an agent's work. It doesn't replace chief (workflow), sage (behavior), or chieftain (runtime) — it adds the missing governance layer.

## License

Apache 2.0
