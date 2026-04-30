#!/usr/bin/env python3
"""Register a new artifact in Council."""

import argparse
import sys
from pathlib import Path


sys.path.insert(0, ".council/scripts")
import council_lib as lib


def main():
    parser = argparse.ArgumentParser(description="Create a Council artifact")
    parser.add_argument("--id", required=True, help="Short slug (e.g., pod-crash)")
    parser.add_argument("--type", required=True, help="Free-form type label")
    parser.add_argument("--risk", required=True, choices=lib.VALID_RISKS, help="Risk level")
    parser.add_argument("--summary", required=True, help="One-line summary")
    parser.add_argument("--script", required=True, help="Path to the script file")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        lib.die(f"Script not found: {args.script}")

    if not script_path.suffix in (".sh", ".py"):
        lib.die(f"Script must be .sh or .py, got: {script_path.suffix}")

    artifact_id = lib.make_artifact_id(args.id)
    artifact_path = lib.artifact_dir(artifact_id)

    # Verify script is inside the artifact directory
    if not str(script_path.resolve()).startswith(str(lib.ARTIFACTS_DIR.resolve())):
        lib.die(f"Script must be inside .council/artifacts/, got: {script_path}")

    event = {
        "id": artifact_id,
        "event": "created",
        "type": args.type,
        "risk": args.risk,
        "summary": args.summary,
        "script": str(script_path),
        "timestamp": lib.now_iso(),
    }
    lib.append_event(event)
    print(f"Created artifact: {artifact_id}")
    print(f"  Type:    {args.type}")
    print(f"  Risk:    {args.risk}")
    print(f"  Summary: {args.summary}")
    print(f"  Script:  {args.script}")


if __name__ == "__main__":
    main()
