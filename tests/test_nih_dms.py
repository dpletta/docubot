from pathlib import Path

from docubot.blocks import get_block
from docubot.metadata.nih_dms import sync_dms_plan
from docubot.metadata.project import ProjectMetadata
from docubot.state import Manifest


def test_sync_dms_plan_blocks(tmp_path: Path):
    dms = tmp_path / "docs" / "DMS.md"
    dms.parent.mkdir(parents=True)
    dms.write_text(
        "# DMS\n\n## 1\n<!-- docubot:dms-data-type -->\nold\n<!-- /docubot:dms-data-type -->\n"
        "## 2\n<!-- docubot:dms-tools-code -->\nx\n<!-- /docubot:dms-tools-code -->\n"
        "## 3\n<!-- docubot:dms-standards -->\nx\n<!-- /docubot:dms-standards -->\n"
        "## 4\n<!-- docubot:dms-preservation -->\nx\n<!-- /docubot:dms-preservation -->\n"
        "## 5\n<!-- docubot:dms-access -->\nx\n<!-- /docubot:dms-access -->\n"
        "## 6\n<!-- docubot:dms-oversight -->\nx\n<!-- /docubot:dms-oversight -->\n",
        encoding="utf-8",
    )
    meta = ProjectMetadata(project_title="test")
    sync_dms_plan(dms, tmp_path, meta, Manifest(), ["data/sample.csv"])
    text = dms.read_text(encoding="utf-8")
    block = get_block(text, "dms-data-type")
    assert block is not None
    assert "tabular" in block or "data_directory" in block or "Detected" in block
