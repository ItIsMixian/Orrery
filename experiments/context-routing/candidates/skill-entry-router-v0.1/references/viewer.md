# Observatory operation

- Windows: `<repo>/start-docsite.bat`
- Cross-platform: `python -X utf8 <repo>/scripts/docsite/serve.py`
- Static build: `python -X utf8 <repo>/scripts/docsite/build_docsite.py`

The static reader is read-only. Dynamic AI features are optional; connection tests may incur provider cost.
Secrets belong only in protected credential storage and must never be echoed, cached in project documents,
or packaged.
