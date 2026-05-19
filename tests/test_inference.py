from docubot.metadata.inference import _sanitize_git_url


def test_sanitize_git_url_strips_token():
    url = "https://x-access-token:secret@github.com/org/repo"
    assert _sanitize_git_url(url) == "https://github.com/org/repo"
