"""Bound a forward keyset scan to an append-only SQLite high-water mark."""

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Cursor:
    feed: str
    ceiling: int
    after: int = 0


@dataclass(frozen=True)
class Page:
    items: tuple[tuple[int, str], ...]
    next_cursor: Cursor | None


class Feed:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS event (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT, feed TEXT NOT NULL, body TEXT NOT NULL
        )""")
        self.db.execute(
            "CREATE INDEX IF NOT EXISTS event_by_feed ON event(feed, sequence)"
        )

    def append(self, feed: str, body: str) -> int:
        with self.db:
            rowid = self.db.execute(
                "INSERT INTO event(feed, body) VALUES (?, ?)", (feed, body)
            ).lastrowid
        assert rowid is not None
        return rowid

    def start(self, feed: str) -> Cursor:
        (ceiling,) = self.db.execute(
            "SELECT COALESCE(MAX(sequence), 0) FROM event WHERE feed = ?", (feed,)
        ).fetchone()
        return Cursor(feed, ceiling)

    def read(self, cursor: Cursor, size: int = 10) -> Page:
        if not 1 <= size <= 100 or not 0 <= cursor.after <= cursor.ceiling:
            raise ValueError("invalid page size or cursor bounds")
        rows = self.db.execute(
            """SELECT sequence, body FROM event
               WHERE feed = ? AND sequence > ? AND sequence <= ? ORDER BY sequence LIMIT ?""",
            (cursor.feed, cursor.after, cursor.ceiling, size + 1),
        ).fetchall()
        next_cursor = (
            Cursor(cursor.feed, cursor.ceiling, rows[size - 1][0])
            if len(rows) > size
            else None
        )
        return Page(tuple(rows[:size]), next_cursor)

    def close(self) -> None:
        self.db.close()


if __name__ == "__main__":
    feed = Feed(":memory:")
    try:
        for body in ("one", "two", "three"):
            feed.append("orders", body)
        cursor = feed.start("orders")
        feed.append("orders", "arrived after cutoff")
        while cursor is not None:
            page = feed.read(cursor, size=2)
            print(page.items)
            cursor = page.next_cursor
    finally:
        feed.close()
