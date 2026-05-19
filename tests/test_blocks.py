from docubot.blocks import get_block, replace_block


def test_replace_block_existing():
    text = "<!-- docubot:foo -->\nold\n<!-- /docubot:foo -->"
    result = replace_block(text, "foo", "new")
    assert "new" in result
    assert "old" not in result


def test_replace_block_append():
    text = "# Title\n"
    result = replace_block(text, "bar", "content")
    assert get_block(result, "bar") == "content"


def test_replace_block_second_of_two():
    text = (
        "<!-- docubot:first -->\na\n<!-- /docubot:first -->\n\n"
        "<!-- docubot:second -->\nb\n<!-- /docubot:second -->\n"
    )
    result = replace_block(text, "second", "updated")
    assert get_block(result, "first") == "a"
    assert get_block(result, "second") == "updated"
