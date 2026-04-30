---
name: council-execute
description: Execute an approved Council artifact
---

# council-execute

Human-only skill. Use this to run an approved artifact's script.

## How to use

```bash
python .council/scripts/council-execute.py ART-001-pod-crash
```

The script runs in a subprocess. stdout, stderr, and exit code are captured and recorded in the event log.

## Before executing

1. Check approved artifacts: `python .council/scripts/council-list.py --status approved`
2. Review the script one more time if needed
3. Execute
