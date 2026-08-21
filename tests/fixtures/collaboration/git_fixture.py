from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


class CollaborationGitFixture:
    """Create a local-only repository topology with no network dependency."""

    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="orrery-collaboration-")
        self.root = Path(self._temporary.name)
        self.repository = self.root / "repository"
        self.worktree_a = self.root / "worktree-a"
        self.worktree_b = self.root / "worktree-b"
        self.clone = self.root / "independent-clone"
        self.environment = dict(os.environ)
        self.environment.update(
            {
                "GIT_AUTHOR_NAME": "Orrery Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Orrery Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                "GIT_CONFIG_NOSYSTEM": "1",
            }
        )
        self._build()

    def close(self) -> None:
        self._temporary.cleanup()

    def __enter__(self) -> "CollaborationGitFixture":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def git(self, cwd: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *arguments],
            env=self.environment,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if check and completed.returncode:
            raise AssertionError(
                f"git {' '.join(arguments)} failed in {cwd}:\n"
                f"{completed.stdout}{completed.stderr}"
            )
        return completed

    def _build(self) -> None:
        self.repository.mkdir()
        self.git(self.repository, "init")
        self.git(self.repository, "branch", "-M", "main")
        (self.repository / "README.md").write_text("# fixture\n", encoding="utf-8")
        (self.repository / ".project-orrery.json").write_text(
            '{"name":"project-orrery","manifest_format":1}\n', encoding="utf-8"
        )
        state = self.repository / "docs" / "state" / "project-structure.md"
        state.parent.mkdir(parents=True)
        state.write_text("# Project structure State\n", encoding="utf-8")
        (self.repository / "AGENTS.md").write_text(
            "# Agent index\n\n"
            "## project structure\n\n"
            "**ID**: `project-structure`\n\n"
            "**Truth**: repository tree.\n\n"
            "**Dig**: [State](docs/state/project-structure.md).\n",
            encoding="utf-8",
        )
        self.git(self.repository, "add", ".")
        self.git(self.repository, "commit", "-m", "fixture baseline")

        self.git(
            self.repository,
            "worktree",
            "add",
            "-b",
            "codex/fixture-a",
            str(self.worktree_a),
            "main",
        )
        self.git(
            self.repository,
            "worktree",
            "add",
            "-b",
            "codex/fixture-b",
            str(self.worktree_b),
            "main",
        )
        untracked = self.worktree_a / "untracked" / "same-path.txt"
        untracked.parent.mkdir()
        untracked.write_text("fixture-only\n", encoding="utf-8")

        self.git(self.root, "clone", str(self.repository), str(self.clone))
        self.git(self.clone, "switch", "-c", "codex/unpushed")
        (self.clone / "clone-only.txt").write_text("not pushed\n", encoding="utf-8")
        self.git(self.clone, "add", "clone-only.txt")
        self.git(self.clone, "commit", "-m", "unpushed fixture branch")
