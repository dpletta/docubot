# Data Management and Sharing Plan

_See NOT-OD-21-014._

<!-- docubot:dms-data-type -->
_Auto-synced 2026-05-20 18:21 UTC_

**Configured types:** software

This repository distributes Python source code, templates, and documentation.
It does not itself generate primary scientific datasets. Docubot helps
research projects maintain NIH DMS plans and FAIR metadata for their data.

**Preserved and shared:**
Source code and documentation are shared via the public Git repository.
Scientific data are not produced by this software project.

**Not shared rationale:**
Not applicable for software-only distribution.

**Detected in repository:**
- Detected modality: `text`

**Related documentation:**
- `docs/ARCHITECTURE.md`
- `docs/DATA_MANAGEMENT_AND_SHARING.md`
- `docs/FAIR_CHECKLIST.md`
- `CHANGELOG.md`
- `metadata/datacite.json`
<!-- /docubot:dms-data-type -->

<!-- docubot:dms-tools-code -->
Python 3.11+, Click, PyYAML. Install with pip install -e .
Cursor hooks and optional git hooks orchestrate documentation sync.

- Package/dependencies: `docubot`
- Source repository: `https://github.com/dpletta/docubot`
<!-- /docubot:dms-tools-code -->

<!-- docubot:dms-standards -->
- Markdown
- YAML (project metadata)
- JSON (DataCite metadata)
- Keep a Changelog
<!-- /docubot:dms-standards -->

<!-- docubot:dms-preservation -->
- **Repository:** GitHub
- **URL:** https://github.com/dpletta/docubot
- **Persistent ID:** _not set — required for FAIR Findable_
- **Share timeline:** Continuous via git; tagged releases as available.
- **Retention:** Indefinite while repository is public.
<!-- /docubot:dms-preservation -->

<!-- docubot:dms-access -->
- **License:** MIT
- **Controlled access:** no
_Document consent, privacy, and reuse limitations per NOT-OD-21-014._
<!-- /docubot:dms-access -->

<!-- docubot:dms-oversight -->
- **Responsible party:** Repository maintainer
- **Review frequency:** At each release and when compliance templates change.
- **Last docubot sync:** 2026-05-19T17:59:08Z
- **Last session finalized:** 2026-05-19T17:26:11Z (`fc67abe4`)
<!-- /docubot:dms-oversight -->
