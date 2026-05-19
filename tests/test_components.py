from docubot.components import components_for_files
from docubot.config import ComponentRule, Config


def test_components_for_files():
    config = Config(
        components=[
            ComponentRule(name="core", paths=["src/docubot/**"]),
            ComponentRule(name="hooks", paths=[".cursor/**"]),
        ]
    )
    found = components_for_files(config, ["src/docubot/cli.py", ".cursor/hooks.json"])
    assert "core" in found
    assert "hooks" in found
