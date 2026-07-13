from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitCandidate:
    id: str
    branch: str
    worktree: Path
    base_revision: str
    candidate_revision: str
    diff: str


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
            self._git("config", "core.autocrlf", "false")

    def ensure_baseline(self) -> str:
        self.initialise()
        try:
            return self._git("rev-parse", "HEAD").strip()
        except subprocess.CalledProcessError:
            self._git("add", "--", ".")
            self._git("commit", "--allow-empty", "-m", "Initialize active OKF bundle")
            return self._git("rev-parse", "HEAD").strip()

    def create_candidate(
        self,
        candidate_id: str,
        worktree: Path | str,
        build: Callable[[Path], None],
    ) -> GitCandidate:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{7,79}", candidate_id):
            raise ValueError("Invalid OKF candidate id")
        base_revision = self.ensure_baseline()
        destination = Path(worktree).resolve()
        if destination.exists():
            raise FileExistsError("OKF candidate worktree already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        branch = f"candidate/{candidate_id}"
        self._git("worktree", "add", "-b", branch, str(destination), base_revision)
        try:
            build(destination)
            self._git_at(destination, "add", "--", ".")
            self._git_at(
                destination,
                "commit",
                "--allow-empty",
                "-m",
                f"Compile OKF candidate {candidate_id}",
            )
            revision = self._git_at(destination, "rev-parse", "HEAD").strip()
            diff = self._git("diff", "--no-ext-diff", base_revision, revision, "--", ".")
            return GitCandidate(
                id=candidate_id,
                branch=branch,
                worktree=destination,
                base_revision=base_revision,
                candidate_revision=revision,
                diff=diff,
            )
        except Exception:
            self._git("worktree", "remove", "--force", str(destination))
            self._git("branch", "-D", branch)
            raise

    def candidate_diff(self, base_revision: str, candidate_revision: str) -> str:
        self.ensure_baseline()
        return self._git("diff", "--no-ext-diff", base_revision, candidate_revision, "--", ".")

    def merge_candidate(self, base_revision: str, candidate_revision: str) -> str:
        self.ensure_baseline()
        lock_path = self.root / ".git" / "agi-okf-merge.lock"
        try:
            descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            raise RuntimeError("Another OKF merge is already in progress") from error
        try:
            os.close(descriptor)
            current = self._git("rev-parse", "HEAD").strip()
            if current != base_revision:
                raise RuntimeError("Candidate base revision is stale")
            self._git("merge", "--ff-only", candidate_revision)
            return self._git("rev-parse", "HEAD").strip()
        finally:
            lock_path.unlink(missing_ok=True)

    @staticmethod
    def _git_at(root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        return result.stdout

    def diff(self) -> str:
        self.initialise()
        self._git("add", "-N", "--", ".")
        return self._git("diff", "--", ".") + self._git("diff", "--cached", "--", ".")

    def commit_approved(self, message: str) -> str:
        self.initialise()
        self._git("add", "--", ".")
        self._git("commit", "-m", message)
        return self._git("rev-parse", "HEAD").strip()
