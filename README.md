# Snapshot Pagination Lab

Resumable keyset pagination over an append-only SQLite feed. The initial request captures a monotonically increasing high-water mark; every page applies it alongside the last-seen row ID. New writes therefore cannot prolong an existing scan, even when the reader reconnects.

```sh
python lab.py
```

The demo prints three original records over two pages, omitting a later append. An index on `(feed, sequence)` supports ordered range scans, with no `OFFSET`. The next cursor is issued only if an extra matching row exists. A cursor is trusted typed application state, not an opaque/authenticated HTTP token or a tenant authorization credential. This approach depends on immutable, non-deleted rows and does not provide snapshot isolation for arbitrary mutable tables.

## Checks

Use Python 3.11 or newer. To reproduce the CI checks in a virtual environment:

```sh
python -m pip install pytest==8.4.2 ruff==0.14.14
ruff check .
ruff format --check .
python -m pytest -q
```
