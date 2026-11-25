import pytest

from lab import Cursor, Feed


@pytest.fixture
def feed(tmp_path):
    instance = Feed(str(tmp_path / "events.db"))
    yield instance
    instance.close()


def test_scan_can_resume_after_reopen_and_excludes_later_inserts(feed):
    ids = [feed.append("a", body) for body in ("x", "y", "z")]
    first = feed.read(feed.start("a"), size=2)
    assert [row[0] for row in first.items] == ids[:2]
    assert first.next_cursor is not None
    path = feed.db.execute("PRAGMA database_list").fetchone()[2]
    other = Feed(path)
    try:
        extra = other.append("a", "new")
        tail = other.read(first.next_cursor, size=2)
        assert tail.items == ((ids[2], "z"),) and tail.next_cursor is None
        assert other.read(other.start("a")).items[-1][0] == extra
    finally:
        other.close()


def test_other_feeds_are_not_returned_and_an_exact_page_terminates(feed):
    a = feed.append("a", "first")
    feed.append("b", "other")
    c = feed.append("a", "second")
    page = feed.read(feed.start("a"), 2)
    assert page.items == ((a, "first"), (c, "second"))
    assert page.next_cursor is None


def test_snapshot_of_empty_feed_stays_empty(feed):
    cursor = feed.start("a")
    feed.append("a", "later")
    assert feed.read(cursor).items == ()


@pytest.mark.parametrize(
    "cursor,size", [(Cursor("a", 1, 2), 10), (Cursor("a", 0), 0), (Cursor("a", 0), 101)]
)
def test_bad_cursor_or_limit(feed, cursor, size):
    with pytest.raises(ValueError):
        feed.read(cursor, size)
