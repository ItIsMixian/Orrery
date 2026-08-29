# Unified Observatory Shell prototype

Status: synthetic-non-authoritative

> **ARCHITECTURE INTERACTION STUDY — NOT A FINAL DOCSITE REDESIGN.** This prototype tests shell navigation,
> capability/mode boundaries and lifecycle language only. The existing production docsite's reading, search, AI Q&A,
> author-document information architecture and recognizable visual experience remain the implementation baseline.

This dependency-light HTML/CSS/JS prototype explores the U1 navigation shell only. It does not consume repository
facts, start a server, configure credentials, enable Team networking, execute Maintenance, select an Authority consumer
or alter any production/public artifact. It is not a production UI specification; any comprehensive visual redesign is
a separate task requiring explicit maintainer approval.

## Compact design brief

- Purpose: show how one visible Orrery URL can make static/dynamic, capability and supervised-helper boundaries obvious.
- Audience/context: maintainers using a dense local documentation and operations workspace.
- Tone: editorial control room, continuing Orrery's dark surfaces, hard dividers, mono evidence and restrained status
  color.
- Differentiator: one persistent navigation rail and visible URL while headless helpers remain lifecycle-managed and
  diagnostically visible without becoming user entrypoints.
- Constraints: dependency-free, synthetic fixture, desktop and 390px mobile, visible focus, reduced motion, no network,
  no ImageGen and no horizontal overflow.

## Run

Serve this directory with any local static server, for example:

```text
python -X utf8 -m http.server 4173 --bind 127.0.0.1 --directory experiments/unified-observatory-shell
```

Open `http://127.0.0.1:4173/`. All controls modify only in-memory synthetic UI state.
