"""Prototype: add NATIVELY-DEPLOYED Ontology + DataAgent items to the healthcare option folder.

Converts the getDefinition export (flattened part paths) into fabric-cicd item folders,
parameterizes the embedded GUIDs via parameter.yml, drops 02_create_ontology, and
rewires GettingStarted to: run 01 (data generator) -> re-save ontology (graph re-ingest).

Run:  python _add_native_items.py <export_dir>
where <export_dir> contains FabricIqOntology.Ontology/, FabricIqOntologyAgent.DataAgent/,
FabricIqDirectAgent.DataAgent/ with '__'-flattened part filenames.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEST = HERE / "fabricdemogallery-fabriciq" / "healthcare"

# Stable logicalIds for the new items (unique within an option folder).
LOGICAL_IDS = {
    "FabricIqOntology.Ontology": "5a1c9b3e-0d4f-4c2a-9e6b-7f8a2d3c4e5f",
    "FabricIqOntologyAgent.DataAgent": "6b2d0c4f-1e5a-4d3b-8f7c-8a9b3e4d5f6a",
    "FabricIqDirectAgent.DataAgent": "7c3e1d5a-2f6b-4e4c-9a8d-9b0c4f5e6a7b",
}

# Export-workspace values -> fabric-cicd dynamic variables (healthcare authoring ws 64e1b413).
PARAM_BLOCK = """  # --- native Ontology/DataAgent items: rewire authoring-workspace refs ---
  # (find_values are globally-unique GUIDs/URIs so no item_type filter is needed)
  - find_value: "64e1b413-b17a-44f8-b452-59d48e00d0d1" # ontology authoring workspace id
    replace_value:
      _ALL_: "$workspace.$id"
  - find_value: "68f6a06c-8344-420a-82b9-9f2da976ac8e" # authoring fabriciq_lakehouse id
    replace_value:
      _ALL_: "$items.Lakehouse.fabriciq_lakehouse.$id"
  - find_value: "eccc3c7a-d7ad-4390-a18d-63fada94960f" # authoring fabriciq_eventhouse id
    replace_value:
      _ALL_: "$items.Eventhouse.fabriciq_eventhouse.$id"
  - find_value: "40b925ec-1c4d-4f2c-bb63-22cccffd5cd1" # authoring KQL database id
    replace_value:
      _ALL_: "$items.KQLDatabase.fabriciq_eventhouse.$id"
  - find_value: "https://trd-nmn1sgfqzhg5c7wk0u.z9.kusto.fabric.microsoft.com" # authoring kusto cluster uri
    replace_value:
      _ALL_: "$items.KQLDatabase.fabriciq_eventhouse.$queryserviceuri"
  - find_value: "509e83d5-cdc8-47b9-ba71-7788441dff81" # authoring FabricIqOntology item id
    replace_value:
      _ALL_: "$items.Ontology.FabricIqOntology.$id"
"""

REFRESH_CELL = '''def _refresh_ontology():
    # Re-save the deployed ontology so the graph re-ingests the freshly loaded data
    # (saving the model triggers ingestion - learn.microsoft.com/fabric/graph/manage-data).
    import time
    import sempy.fabric as fabric
    _c = fabric.FabricRestClient()
    _ws = fabric.get_workspace_id()
    _items = _c.get(f"/v1/workspaces/{_ws}/items").json()["value"]
    _ont = next(_i for _i in _items if _i["type"] == "Ontology")
    _d = _c.post(f"/v1/workspaces/{_ws}/items/{_ont['id']}/getDefinition")
    if _d.status_code == 202:
        _loc = _d.headers["Location"]
        while True:
            _s = _c.get(_loc)
            if _s.json().get("status") in ("Succeeded", "Failed"):
                break
            time.sleep(2)
        _d = _c.get(_loc + "/result")
    _r = _c.post(f"/v1/workspaces/{_ws}/items/{_ont['id']}/updateDefinition",
                 json={"definition": _d.json()["definition"]})
    print(f"Ontology re-saved (graph re-ingestion triggered): HTTP {_r.status_code}")

print(f"Industry: {INDUSTRY}")'''


def unflatten(export_dir: Path) -> None:
    for item_name in LOGICAL_IDS:
        src = export_dir / item_name
        if not src.is_dir():
            raise SystemExit(f"missing export folder: {src}")
        dst = DEST / item_name
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        for f in src.iterdir():
            rel = f.name.replace("__", "/")
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if f.name == ".platform":
                platform = json.loads(f.read_text(encoding="utf-8"))
                platform["config"]["logicalId"] = LOGICAL_IDS[item_name]
                target.write_text(json.dumps(platform, indent=2) + "\n", encoding="utf-8")
            else:
                target.write_bytes(f.read_bytes())
        print(f"item folder written: {dst.relative_to(HERE)}")


def patch_parameter_yml() -> None:
    p = DEST / "parameter.yml"
    text = p.read_text(encoding="utf-8")
    if "native Ontology/DataAgent" in text:
        print("parameter.yml already patched")
        return
    p.write_text(text.rstrip() + "\n" + PARAM_BLOCK, encoding="utf-8")
    print("parameter.yml patched")


def drop_02_and_patch_gettingstarted() -> None:
    nb02 = DEST / "02_create_ontology.Notebook"
    if nb02.exists():
        shutil.rmtree(nb02)
        print("removed 02_create_ontology.Notebook")

    gs = DEST / "GettingStarted.Notebook" / "notebook-content.py"
    src = gs.read_text(encoding="utf-8")

    src = src.replace(
        '''| `01_generate_ontology_data` | Notebook | Loads sample data into the Lakehouse + Eventhouse |
# | `02_create_ontology` | Notebook | Builds the ontology, binds it, and creates two Data Agents |''',
        '''| `01_generate_ontology_data` | Notebook | Loads sample data into the Lakehouse + Eventhouse |
# | `FabricIqOntology` | Ontology | The semantic model, bound to the Lakehouse + Eventhouse tables |
# | `FabricIqOntologyAgent` | Data Agent | Answers questions through the ontology |
# | `FabricIqDirectAgent` | Data Agent | Baseline agent over the raw tables |''',
    )
    src = src.replace(
        "# Pressing **Run all** runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.",
        "# The **Ontology** and both **Data Agents** are deployed natively. Pressing **Run all** loads the sample data (`01_generate_ontology_data`) and re-saves the ontology so its graph ingests the data.",
    )
    src = src.replace(
        '''print(f"Industry: {INDUSTRY}")''',
        REFRESH_CELL,
        1,
    )
    src = src.replace(
        '''_run_step("01_generate_ontology_data")
_run_step("02_create_ontology")
print("All steps complete.")''',
        '''_run_step("01_generate_ontology_data")
_refresh_ontology()
print("All steps complete.")''',
    )
    gs.write_text(src, encoding="utf-8")
    print("GettingStarted patched (data generator + ontology re-save only)")


if __name__ == "__main__":
    export = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        r"C:\Users\omerguzel\fabric-jumpstart\src\fabric_jumpstart\dev\_ontology_export"
    )
    unflatten(export)
    patch_parameter_yml()
    drop_02_and_patch_gettingstarted()
    print("done.")
