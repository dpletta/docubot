from docubot.metadata.inference import _sanitize_git_url, detect_package_name


def test_sanitize_git_url_strips_token():
    url = "https://x-access-token:secret@github.com/org/repo"
    assert _sanitize_git_url(url) == "https://github.com/org/repo"


def test_detect_package_name_reads_project_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.example]
name = "wrong-section"

[project]
name = "right-package"
""",
        encoding="utf-8",
    )

    assert detect_package_name(tmp_path) == "right-package"
