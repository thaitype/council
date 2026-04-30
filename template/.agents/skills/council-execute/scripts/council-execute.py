#!/usr/bin/env python3
"""Execute an approved Council artifact."""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".council/scripts")
import council_lib as lib

TIMEOUT_SECONDS = 120


def main():
    parser = argparse.ArgumentParser(description="Execute an approved Council artifact")
    parser.add_argument("artifact_id", help="Artifact ID (e.g., ART-001-pod-crash)")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS, help=f"Timeout in seconds (default: {TIMEOUT_SECONDS})")
    args = parser.parse_args()

    art = lib.get_artifact(args.artifact_id)
    if not art:
        lib.die(f"Artifact not found: {args.artifact_id}")

    state = lib.get_current_state(args.artifact_id)
    if state != "approved":
        lib.die(f"Artifact is '{state}', expected 'approved' for execution")

    script_path = Path(art["script"])
    if not script_path.exists():
        lib.die(f"Script not found: {script_path}")

    # Determine how to run the script
    if script_path.suffix == ".sh":
        cmd = ["bash", str(script_path)]
    elif script_path.suffix == ".py":
        cmd = [sys.executable, str(script_path)]
    else:
        lib.die(f"Unsupported script type: {script_path.suffix}")

    print(f"Executing: {args.artifact_id}")
    print(f"  Script: {script_path}")
    print(f"  Timeout: {args.timeout}s")
    print("---")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=args.timeout,
            cwd=str(lib.COUNCIL_ROOT.parent),  # Run from project root
        )
        stdout = result.stdout
        stderr = result.stderr
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        stdout = ""
        stderr = f"Timeout after {args.timeout} seconds"
        exit_code = -1

    # Print output
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    print("---")
    print(f"Exit code: {exit_code}")

    # Record event
    event = {
        "id": args.artifact_id,
        "event": "executed",
        "exit_code": exit_code,
        "stdout": stdout[:2000],  # Truncate for JSONL sanity
        "stderr": stderr[:2000],
        "timestamp": lib.now_iso(),
    }
    lib.append_event(event)

    if exit_code == 0:
        print(f"Success: {args.artifact_id}")
    else:
        print(f"Failed: {args.artifact_id} (exit code {exit_code})")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
