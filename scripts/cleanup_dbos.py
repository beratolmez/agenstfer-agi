import os
import shutil
from pathlib import Path

def force_remove(path_str):
    p = Path(path_str)
    if not p.exists():
        print(f"Not found: {p}")
        return
    if p.is_dir():
        shutil.rmtree(p)
        print(f"Removed dir: {p}")
    else:
        p.unlink()
        print(f"Removed file: {p}")

if __name__ == "__main__":
    base = Path(__file__).parent.parent
    targets = [
        "apps/api/legacy_agi_server",
        "apps/api/tests/test_workflow_compatibility.py",
        "apps/api/tests/test_workflow_platform.py",
        "docs/adr/0002-pydantic-ai-dbos.md",
        "docs/adr/0011-bounded-task-orchestration.md",
        "scripts/watch-workflow-restarts.sh"
    ]
    for t in targets:
        force_remove(base / t)
