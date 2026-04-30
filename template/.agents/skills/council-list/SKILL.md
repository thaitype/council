---
name: council-list
description: List and inspect Council artifacts
---

# council-list

Use this to view artifacts and their current status.

## How to use

List all artifacts:

```bash
python .agents/skills/council-list/scripts/council-list.py
```

Filter by status:

```bash
python .agents/skills/council-list/scripts/council-list.py --status pending
python .agents/skills/council-list/scripts/council-list.py --status approved
python .agents/skills/council-list/scripts/council-list.py --status executed
python .agents/skills/council-list/scripts/council-list.py --status rejected
```

Show detail for one artifact:

```bash
python .agents/skills/council-list/scripts/council-list.py --id ART-001-pod-crash
```
