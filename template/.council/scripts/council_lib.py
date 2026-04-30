"""Council shared library — JSONL state management and artifact utilities."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


COUNCIL_ROOT = Path(".council").resolve()
ARTIFACTS_DIR = COUNCIL_ROOT / "artifacts"
DATA_DIR = COUNCIL_ROOT / "data"
JSONL_FILE = DATA_DIR / "artifacts.jsonl"

VALID_RISKS = ("low", "medium", "high")
VALID_EVENTS = ("created", "approved", "rejected", "executed")


def ensure_dirs():
    """Create required directories if they don't exist."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def read_events() -> list[dict]:
    """Read all events from the JSONL file."""
    if not JSONL_FILE.exists():
        return []
    events = []
    with open(JSONL_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def append_event(event: dict):
    """Append a single event to the JSONL file."""
    ensure_dirs()
    with open(JSONL_FILE, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def next_sequence_number() -> int:
    """Get the next artifact sequence number from existing events."""
    events = read_events()
    max_num = 0
    for e in events:
        if e.get("event") == "created":
            art_id = e.get("id", "")
            # Extract number from ART-XXX-slug
            parts = art_id.split("-")
            if len(parts) >= 2:
                try:
                    num = int(parts[1])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
    return max_num + 1


def make_artifact_id(slug: str) -> str:
    """Generate artifact ID: ART-XXX-slug."""
    seq = next_sequence_number()
    return f"ART-{seq:03d}-{slug}"


def get_current_state(artifact_id: str) -> str | None:
    """Derive current state of an artifact from event log."""
    events = read_events()
    state = None
    for e in events:
        if e.get("id") == artifact_id:
            event_type = e.get("event")
            if event_type in VALID_EVENTS:
                state = event_type
    return state


def get_artifact(artifact_id: str) -> dict | None:
    """Get the creation event for an artifact."""
    events = read_events()
    for e in events:
        if e.get("id") == artifact_id and e.get("event") == "created":
            return e
    return None


def list_artifacts(status_filter: str | None = None) -> list[dict]:
    """List all artifacts with their current state."""
    events = read_events()
    # Collect creation events
    artifacts = {}
    for e in events:
        art_id = e.get("id")
        if e.get("event") == "created":
            artifacts[art_id] = {**e, "current_state": "created"}
    # Apply state transitions
    for e in events:
        art_id = e.get("id")
        if art_id in artifacts and e.get("event") in VALID_EVENTS:
            artifacts[art_id]["current_state"] = e["event"]
    result = list(artifacts.values())
    if status_filter:
        result = [a for a in result if a["current_state"] == status_filter]
    return result


def now_iso() -> str:
    """Current timestamp in ISO format with timezone."""
    return datetime.now(timezone.utc).astimezone().isoformat()


def artifact_dir(artifact_id: str) -> Path:
    """Path to an artifact's directory."""
    return ARTIFACTS_DIR / artifact_id


def die(msg: str):
    """Print error and exit."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)
