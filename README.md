# Fabric Jumpstart — FabricIQ Ontology + Data Agent

Content repository for the **FabricIQ Ontology** Fabric Jumpstart, installed via
[fabric-jumpstart](https://github.com/microsoft/fabric-jumpstart):

```python
import fabric_jumpstart as jumpstart
jumpstart.install("fabricdemogallery-fabriciq")
```

## What it deploys
- `fabriciq_lakehouse` (Lakehouse) — business entities as Delta tables
- `fabriciq_eventhouse` (Eventhouse, with its KQL database) — time-series as KQL tables
- `01_generate_ontology_data`, `02_create_ontology`, `GettingStarted` (Notebooks)

Start at the **`GettingStarted`** notebook: run it, pick an industry from the
dropdown, and click **Build the demo**. It runs `01` (data load) and `02`
(ontology build) for you and links the created items. `02` builds the
**FabricIqOntology** item and two **Data Agents** (ontology-grounded vs. direct)
so you can compare answer quality on the same questions.

> **Prerequisite:** Fabric IQ / Ontology (preview) enabled in your tenant.

## Layout
- `fabricdemogallery-fabriciq/` — the jumpstart (`workspace_path`); Fabric items sync here.
- `fabricdemogallery-fabriciq/data/` — accelerator wheel + one ontology package (`.iq`) per
  industry; the notebooks download the selected package from this repo at runtime.
- `fabricdemogallery-fabriciq/jumpstart.yml` — mirror of the registry entry contributed to
  the `microsoft/fabric-jumpstart` registry.
- `fabricdemogallery-fabriciq/parameter.yml` — fabric-cicd deployment parameterization
  (rebinds the notebooks' default lakehouse to the target workspace).

The notebooks are self-configuring: they resolve the wheel/`.iq` paths and the
Eventhouse cluster URI from the current workspace at runtime (no manual patching).
