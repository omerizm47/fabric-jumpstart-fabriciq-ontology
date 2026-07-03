# Fabric Jumpstart — FabricIQ Ontology + Data Agent

Content repository for the **FabricIQ Ontology** Fabric Jumpstart, installed via
[fabric-jumpstart](https://github.com/microsoft/fabric-jumpstart):

```python
import fabric_jumpstart as jumpstart
jumpstart.install("fabricdemogallery-fabriciq", install_option="healthcare")
```

One command, one industry choice, zero manual steps. Twelve industries are
available as install options: `construction`, `education`, `energy-grid`,
`financial-services`, `healthcare`, `hospitality`, `manufacturing-qc`, `media`,
`professional-services`, `retail-sales`, `technology`, `transportation`.

## What it deploys

Everything is deployed **natively by fabric-cicd** from the committed item
definitions of the selected industry:

| Item | Type | Purpose |
|---|---|---|
| `fabriciq_lakehouse` | Lakehouse | Business entities as Delta tables |
| `fabriciq_eventhouse` | Eventhouse + KQL database | Time-series as KQL tables |
| `FabricIqOntology` | Ontology | Semantic model bound to the Lakehouse + Eventhouse tables |
| `FabricIqOntologyAgent` | Data Agent | Answers questions through the ontology |
| `FabricIqDirectAgent` | Data Agent | Baseline agent over the raw tables |
| `GettingStarted` | Notebook | Documentation and links (nothing to run) |

The sample data is loaded during install by the installer's declarative
`data_load` block: the industry's `.iq` package is read from this repository,
event timestamps are shifted so the newest land ~yesterday, tables are loaded
into the Lakehouse and Eventhouse, and the ontology is re-saved so its graph
ingests the data.

After install, open the two **Data Agents** and ask both the same question —
the ontology-grounded agent understands entity relationships and time-series
context; the direct agent typically cannot join the two sources.

> **Prerequisite:** Fabric IQ / Ontology (preview) enabled in your tenant.

## Layout

- `fabricdemogallery-fabriciq/<industry>/` — one complete fabric-cicd source per
  install option: the Lakehouse, Eventhouse (with KQL database), the Ontology,
  both Data Agents, the docs-only `GettingStarted` notebook, and a
  `parameter.yml` that rewires all authoring-workspace references to the target
  workspace at deploy time (`$workspace.$id`, `$items.<type>.<name>.$id`,
  `$items.Eventhouse.<name>.$queryserviceuri`).
- `fabricdemogallery-fabriciq/data/` — one ontology package (`.iq`) per industry;
  the installer's `data_load` reads the selected package from the cloned repo.
- `fabricdemogallery-fabriciq/jumpstart.yml` — mirror of the registry entry
  contributed to the `microsoft/fabric-jumpstart` registry.
- `tools/` — authoring pipeline:
  - `promote_native.py <industry> <authoring_workspace_id>` exports a built
    ontology + agents from an authoring workspace into the industry's option
    folder (definitions via `getDefinition`, GUIDs parameterized).
  - `verify_native_layout.py` validates all twelve option folders are complete
    and consistent.

## Authoring a new or updated industry

1. Deploy the industry once into a scratch workspace and build its ontology
   (any flow that produces `FabricIqOntology` + the two agents).
2. `python tools/promote_native.py <industry> <workspace_id>`
3. `python tools/verify_native_layout.py`
4. Commit and tag; the registry pins tags, never branches.
