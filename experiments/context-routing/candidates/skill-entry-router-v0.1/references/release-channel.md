# Release and compatibility operation

For maintenance that depends on Orrery version compatibility, run the cached, read-only release checker.
Network failure must not block unrelated documentation work. Treat Skill version, target toolchain,
project-manifest format and document schema as separate surfaces.

Never install silently. Obtain an exact tagged release, verify its checksum, validate it, compare local
changes and back up the installed Skill before replacement. Updating the Skill and upgrading target viewer
tools are separate approvals. Preview `--upgrade-tools`, review backup paths, then apply explicitly.
