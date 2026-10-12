# Data access and public download scope

Permission for public release of patient-derived data has not yet been documented and verified for a defined set of files. No patient-derived data are included in this release. Willingness to share and de-identification are not evidence of institutional, ethics or third-party authorization to redistribute a defined dataset. The earlier release documentation overstated this permission status; its tag is retained, and this correction is recorded in a new commit.

Public downloads contain MIT-licensed code, configurations, input schemas and synthetic tests. The software license does not license clinical data. There is no clinical-data download address or data DOI. This page is an access-information page, not a data repository or a guarantee of access.

## Candidate input levels under review

The private review inventory contains 15 candidates: eight frozen numerical source tables underlying Tables S1–S6 and S8; static array values; action-level and pooled five-window beta values; action-level and pooled beta time courses; independently confirmed contact/channel order; and fixed display limits. These have not been approved for public redistribution. Display coordinates indicate strip/contact order, not patient MRI locations. Minimal dependencies are specified in MINIMAL_INPUTS.md and `render_figures.py --list-inputs`.

Frozen source tables can recover reported observations and saved uncertainty summaries; they cannot reconstruct event-level estimation or regenerate resampling uncertainty. Re-estimation additionally needs authorized keyed event arrays and saved complete-round indices, which are outside this minimum candidate inventory. Raw EDF/BOLD processing is not provided. Raw recordings, original or derived clinical images, operative/navigation materials and identity links are outside the current candidate scope.

## Contact and access conditions

A named public data-request contact, institutional role, email, eligible uses, approval route and data-use agreement conditions have not yet been confirmed by the responsible author. An operational clinical-data request route therefore remains unresolved; no approval authority, eligibility promise or response deadline is asserted here. The manuscript's corresponding-author status alone is not assigned data-approval responsibility. Do not post patient information, signatures, permission documents or restricted inputs in GitHub issues.

The software can be downloaded and tested without clinical-data permission. A future public or controlled data delivery must identify the exact approved files/fields, applicable license or access conditions, responsible authority and matching code commit. Approval documents and patient signatures will not be included in the public repository.
