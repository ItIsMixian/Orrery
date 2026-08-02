# Project Orrery

Project Orrery turns a repository's Markdown documentation into a living project observatory: decisions remain historical, current state stays factual, implementation plans stay provisional, and validation closes the loop.

It ships as a portable Codex skill plus a project template. The generated local site provides a searchable single-file reader, decision/state navigation, document health signals, optional AI-assisted Q&A, roadmap synthesis, and a GitHub trend radar.

## Install the skill

Copy `skills/project-orrery` into your Codex skills directory, or install this repository with the Codex skill installer once it is hosted on GitHub.

Then ask Codex:

> Use Project Orrery to scaffold a documentation observatory in this repository.

## Direct use

```powershell
python skills/project-orrery/scripts/install_project_orrery.py --target D:\path\to\project --title "My Project"
```

Existing authored documentation is never overwritten by the default scaffold operation. The copied adoption document is only a proposal: installation does not silently declare the authority model accepted. To refresh viewer files on Orrery's upgrade whitelist, add `--upgrade-tools`; changed files are backed up first.

After installation:

```powershell
cd D:\path\to\project
python -m pip install -r scripts/docsite/requirements.txt
.\start-docsite.bat
```

First validate the scaffold without dependencies:

```powershell
python skills/project-orrery/scripts/validate_installation.py --target D:\path\to\project
```

After installing the viewer dependencies, add `--build`. Use `--require-integrated` only after the target repository has accepted its own adoption ADR and updated its real `AGENTS.md`, progress, and state documents.

The v0.1 reader UI is Chinese-first while project content can use any language.

## Documentation model

```text
Product intent -> Seed/principles -> ADR -> approved Design -> Implementation Plan
                                      |                              |
                                      +----------> implementation <--+
                                                        |
                                                     State Docs
                                                        |
                                                    Validation
                                                        |
                                                     Snapshot
```

Library and Backlog feed proposals; they do not constrain implementation until a decision is accepted. `accepted` never means `implemented`.

## License

MIT
