# Council — Agent Rules

> All actions go through artifacts. No direct execution.

## Core Rule

You do NOT run bash commands directly. Instead, you produce **artifacts** — scripts that a human reviews and executes.

If the project runs in a sandbox, you may explore freely within the sandbox scope. But any action intended for production MUST go through the artifact workflow.

If the project runs WITHOUT a sandbox, ALL bash commands are denied. Everything goes through artifacts.

## Artifact Workflow

1. Do your research and analysis
2. Write a script (`.sh` or `.py`) to `.council/artifacts/<slug>/`
3. Register it: `python .agents/skills/council-create/scripts/council-create.py --id <slug> --type <type> --risk <low|medium|high> --summary "..." --script <path>`
4. Wait for human review

## Artifact Sizing

- **Too small** — A single exploration command like `ls -la` or `cat file.txt` is NOT an artifact. Just ask the human or describe what you need.
- **Too big** — A 200-line script doing 10 things is too much for a human to review confidently. Break it into smaller artifacts.
- **Right size** — Concise. Has enough context for a human to make a yes/no decision. If the human can't decide from reading it, create a new artifact with more detail.

## Available Skills

- `council-create` — Submit work as an artifact
- `council-list` — View artifacts and their status
- `council-review` — (human) Approve or reject artifacts
- `council-execute` — (human) Run approved artifacts

## Sandbox vs No-Sandbox

### With Sandbox

You have an isolated environment to explore and test. Run commands freely within the sandbox. Use artifacts only for actions that will affect production.

### Without Sandbox

You have no isolated environment. Do not run any bash commands. Produce all work as artifacts for human review.

### Configuring Permissions

Use your coding agent's native permission system to enforce this:

**Claude Code** — `settings.local.json`:
```json
{
  "permissions": {
    "deny": ["Bash(*)"],
    "allow": [
      "Bash(python .agents/skills/council-create/scripts/council-create.py *)",
      "Bash(python .agents/skills/council-list/scripts/council-list.py *)"
    ]
  }
}
```

**Other agents** — Configure according to your agent's permission documentation.
