from docubot.stale import _matches_watch


def test_matches_watch_glob():
    assert _matches_watch("src/foo.py", ["src/**", "*.py"])
    assert not _matches_watch("docs/readme.md", ["src/**"])
