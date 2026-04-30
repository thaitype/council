---
name: council-create
description: Submit work as a Council artifact for human review
---

# council-create

Use this skill when you have produced actionable work (a script, a fix, a migration) that needs human approval before execution.

## How to use

1. Create the artifact directory and write your script:

```bash
mkdir -p .council/artifacts/<slug>
# Write your script file (e.g., fix.sh or migrate.py)
```

2. Register the artifact:

```bash
python .council/scripts/council-create.py --id <slug> --type <type> --risk <low|medium|high> --summary "<what and why>" --script .council/artifacts/<slug>/<script-file>
```

## Arguments

- `--id` — short slug describing the artifact (e.g., `pod-crash`, `update-deps`)
- `--type` — free-form label (e.g., `remediation`, `code-change`, `migration`, `investigation`)
- `--risk` — `low`, `medium`, or `high`
- `--summary` — one-line description of what the script does and why
- `--script` — path to the script file you already wrote

## Rules

- Write the script file BEFORE calling this command
- One script per artifact — if you need multiple steps, create multiple artifacts
- Keep scripts concise — enough information for a human to make a decision
- Do NOT create artifacts for trivial exploration (e.g., `ls -la`)
- Do NOT create massive scripts — break them into smaller artifacts
