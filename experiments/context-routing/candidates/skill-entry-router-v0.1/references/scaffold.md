# Scaffold operation

1. Inspect the target root, local `AGENTS.md`, documentation directories and worktree status.
2. Identify the documentation authority root; do not move implementation to fit a template.
3. Preview with `install_project_orrery.py --target <repo> --title <title> --dry-run`.
4. Review every skip, upgrade and mixed-toolchain warning, then install without overwriting authored files.
5. Existing repositories require a project-specific adoption ADR and real entrance/State updates before
   claiming authority integration. Generated proposals are not accepted decisions.
6. Run dependency-free validation first. Install viewer requirements and run `--build` only when the viewer
   is in scope.

