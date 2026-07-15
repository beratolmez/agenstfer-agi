#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from agi_server.release_evidence import (
    ReleaseEvidenceError,
    build_release_manifest,
    load_json_object,
    validate_qualification_report,
    validate_restart_evidence,
)


def _artifact(value: str) -> tuple[str, Path]:
    name, separator, raw_path = value.partition("=")
    if not separator or not name or not raw_path:
        raise argparse.ArgumentTypeError("Artifacts use NAME=PATH")
    return name, Path(raw_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate content-safe MVP release evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    qualification = subparsers.add_parser("qualification")
    qualification.add_argument("--input", type=Path, required=True)
    qualification.add_argument("--profile", required=True)
    qualification.add_argument("--minimum-attempts", type=int, default=20)

    restart = subparsers.add_parser("restart")
    restart.add_argument("--input", type=Path, required=True)
    restart.add_argument("--workflow-id", required=True)

    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("--steps", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.add_argument("--started-at", required=True)
    manifest.add_argument("--exit-code", type=int, required=True)
    manifest.add_argument("--model-profile", required=True)
    manifest.add_argument("--artifact", action="append", default=[], type=_artifact)

    args = parser.parse_args()
    try:
        if args.command == "qualification":
            summary = validate_qualification_report(
                load_json_object(args.input),
                expected_profile=args.profile,
                minimum_attempts=args.minimum_attempts,
            )
        elif args.command == "restart":
            summary = validate_restart_evidence(
                load_json_object(args.input),
                expected_workflow_id=args.workflow_id,
            )
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True, encoding="utf-8"
            ).strip()
            summary = build_release_manifest(
                steps_path=args.steps,
                output_path=args.output,
                started_at=args.started_at,
                exit_code=args.exit_code,
                git_commit=commit,
                model_profile=args.model_profile,
                artifacts=dict(args.artifact),
            )
            args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        if args.command == "manifest" and args.exit_code == 0 and summary["result"] != "passed":
            return 1
        return 0
    except ReleaseEvidenceError as error:
        print(f"Release evidence rejected: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
