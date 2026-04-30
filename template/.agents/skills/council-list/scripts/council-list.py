#!/usr/bin/env python3
"""List and inspect Council artifacts."""

import argparse
import sys
from pathlib import Path


sys.path.insert(0, ".council/scripts")
import council_lib as lib


def show_detail(artifact_id: str):
    """Show detailed info for a single artifact."""
    art = lib.get_artifact(artifact_id)
    if not art:
        lib.die(f"Artifact not found: {artifact_id}")

    state = lib.get_current_state(artifact_id)
    print(f"ID:      {art['id']}")
    print(f"State:   {state}")
    print(f"Type:    {art['type']}")
    print(f"Risk:    {art['risk']}")
    print(f"Summary: {art['summary']}")
    print(f"Script:  {art['script']}")
    print(f"Created: {art['timestamp']}")

    # Show event history
    print("\nHistory:")
    for e in lib.read_events():
        if e.get("id") == artifact_id:
            event = e["event"]
            ts = e["timestamp"]
            extra = ""
            if e.get("comment"):
                extra = f" — {e['comment']}"
            if e.get("approver"):
                extra = f" by {e['approver']}{extra}"
            if e.get("exit_code") is not None:
                extra = f" exit={e['exit_code']}{extra}"
            print(f"  [{ts}] {event}{extra}")


def show_list(status_filter: str | None):
    """Show summary list of artifacts."""
    artifacts = lib.list_artifacts(status_filter)
    if not artifacts:
        print("No artifacts found.")
        return

    for art in artifacts:
        state = art["current_state"]
        risk = art["risk"]
        summary = art["summary"]
        print(f"  {art['id']}  [{state}]  risk={risk}  {summary}")


def main():
    parser = argparse.ArgumentParser(description="List Council artifacts")
    parser.add_argument("--status", choices=["created", "approved", "rejected", "executed"], help="Filter by status")
    parser.add_argument("--id", help="Show detail for a specific artifact")
    args = parser.parse_args()

    if args.id:
        show_detail(args.id)
    else:
        show_list(args.status)


if __name__ == "__main__":
    main()
