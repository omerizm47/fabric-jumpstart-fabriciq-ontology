# Fabric Jumpstart — FabricIQ Ontology + Data Agent

Content repository for the **FabricIQ Ontology** Fabric Jumpstart, installed via
[fabric-jumpstart](https://github.com/microsoft/fabric-jumpstart):

```python
import fabric_jumpstart as jumpstart
jumpstart.install("fabricdemogallery-fabriciq")
```

## What it deploys
- `fabriciq_lakehouse` (Lakehouse) — business entities as Delta tables
- `fabriciq_eventhouse` (Eventhouse) — time-series as KQL tables
- `01_generate_ontology_data`, `02_create_ontology`, `GettingStarted` (Notebooks)

Running `02_create_ontology` builds the **FabricIqOntology** item and two grounded
**Data Agents** (ontology-grounded vs. direct) so you can compare answer quality.
Start at the **`GettingStarted`** notebook.

> **Prerequisite:** Fabric IQ / Ontology (preview) enabled in your tenant.

## Layout
- `fabricdemogallery-fabriciq/` — the jumpstart (`workspace_path`); Fabric items sync here.
- `fabricdemogallery-fabriciq/data/` — accelerator wheel + ontology `.iq` (`files_source_path`,
  auto-uploaded to the lakehouse `Files/` after deployment).
- `fabricdemogallery-fabriciq/jumpstart.yml` — the registry-entry draft (the live entry is
  contributed to the `microsoft/fabric-jumpstart` registry).

The notebooks are self-configuring: they resolve the wheel/`.iq` paths and the
Eventhouse cluster URI from the current workspace at runtime (no manual patching).
