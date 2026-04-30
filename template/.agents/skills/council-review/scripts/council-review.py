#!/usr/bin/env python3
"""Approve or reject a Council artifact."""

import argparse
import sys

sys.path.insert(0, ".council/scripts")
import council_lib as lib


def main():
    parser = argparse.ArgumentParser(description="Review a Council artifact")
    parser.add_argument("artifact_id", help="Artifact ID (e.g., ART-001-pod-crash)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--approve", action="store_true", help="Approve the artifact")
    group.add_argument("--reject", action="store_true", help="Reject the artifact")
    parser.add_argument("--comment", default="", help="Review comment")
    parser.add_argument("--approver", default="human", help="Approver name")
    args = parser.parse_args()

    art = lib.get_artifact(args.artifact_id)
    if not art:
        lib.die(f"Artifact not found: {args.artifact_id}")

    state = lib.get_current_state(args.artifact_id)
    if state != "created":
        lib.die(f"Artifact is '{state}', expected 'created' for review")

    event_type = "approved" if args.approve else "rejected"
    event = {
        "id": args.artifact_id,
        "event": event_type,
        "approver": args.approver,
        "comment": args.comment,
        "timestamp": lib.now_iso(),
    }
    lib.append_event(event)

    action = "Approved" if args.approve else "Rejected"
    print(f"{action}: {args.artifact_id}")
    if args.comment:
        print(f"  Comment: {args.comment}")


if __name__ == "__main__":
    main()
