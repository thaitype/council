---
name: council-review
description: Approve or reject a Council artifact
---

# council-review

Human-only skill. Use this to approve or reject a pending artifact.

## How to use

Approve an artifact:

```bash
python .agents/skills/council-review/scripts/council-review.py ART-001-pod-crash --approve
python .agents/skills/council-review/scripts/council-review.py ART-001-pod-crash --approve --comment "looks good"
```

Reject an artifact:

```bash
python .agents/skills/council-review/scripts/council-review.py ART-001-pod-crash --reject --comment "too risky"
```

## Before reviewing

1. Check what's pending: `python .agents/skills/council-list/scripts/council-list.py --status created`
2. Read the script file to understand what it does
3. Approve or reject with a comment
