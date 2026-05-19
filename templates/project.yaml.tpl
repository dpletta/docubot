# Docubot project metadata (NIH DMS + FAIR source of truth)
# Guidance: NOT-OD-21-014 Elements of an NIH Data Management and Sharing Plan
# https://grants.nih.gov/grants/guide/notice-files/NOT-OD-21-014.html

project:
  title: "${project_name}"
  description: ""
  version: "0.1.0"

creators:
  - name: ""
    orcid: ""
    affiliation: ""
    role: contact  # contact | contributor | principal_investigator

funding:
  - agency: NIH
    grant_id: ""  # e.g. R01GM123456

license: MIT

data:
  # Element 1: Data Type
  types: []  # e.g. survey, imaging, genomic, tabular
  types_narrative: |
    Describe scientific data to be managed, preserved, and shared.
  preserved_and_shared: |
    Which data will be preserved and shared.
  not_shared_rationale: |
    Rationale for data not shared (ethics, legal, technical).
  related_documentation:
    - docs/ARCHITECTURE.md
    - CHANGELOG.md

  # Element 2: Related Tools, Software and/or Code
  tools_code: |
    Describe tools needed to access or reuse data (open source, commercial, team-only).

  # Element 3: Standards
  standards: []  # e.g. CSV, JSON, DICOM, FHIR

  # Element 4: Data Preservation, Access, and Associated Timelines
  repository:
    name: ""
    url: ""
    persistent_id: ""  # DOI or other PID for FAIR Findable
    share_timeline: "As soon as possible after publication or end of award."
    retention_period: ""

  # Element 5: Access, Distribution, or Reuse Considerations
  access:
    license: MIT
    controlled_access: false
    restrictions: ""
    consent_notes: ""
    privacy_notes: ""

# Element 6: Oversight of Data Management and Sharing
oversight:
  responsible_party: ""
  review_frequency: "Annually or at major project milestones."
