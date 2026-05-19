from docubot.providers.openai_compat import _redact


def test_redact_masks_sensitive_lines_only():
    text = "Files: src/app.py\nToken: abc123\nSummary: keep this context"

    assert _redact(text) == "Files: src/app.py\n[redacted line]\nSummary: keep this context"
