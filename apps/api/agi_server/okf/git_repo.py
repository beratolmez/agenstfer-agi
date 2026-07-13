from __future__ import annotations

import subprocess
from pathlib import Path


class GitKnowledgeRepository:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        return result.stdout

    def initialise(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / ".git").exists():
            self._git("init", "--initial-branch=main")
            self._git("config", "user.name", "Growth Intelligence")
            self._git("config", "user.email", "growth-intelligence@localhost")

    def diff(self) -> str:
        self.initialise()
        self._git("add", "-N", "--", ".")
        return self._git("diff", "--", ".") + self._git("diff", "--cached", "--", ".")

    def commit_approved(self, message: str) -> str:
        self.initialise()
        self._git("add", "--", ".")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD").strip()
