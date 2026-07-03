"""Promote an industry to the NATIVE one-step layout.

Reads the authored Ontology + Data Agents from a build workspace (where the
runtime flow ran once), writes them into the industry's option folder, extends
parameter.yml with the authoring GUIDs -> dynamic variables, removes the
runtime notebooks, and rewrites GettingStarted as docs-only.

Usage:  python _promote_native.py <industry> <authoring_workspace_id>
"""

from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

HERE = Path(__file__).parent
ROOT = HERE.parent / "fabricdemogallery-fabriciq"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
NS = uuid.UUID("a7c1b2d3-e4f5-4a6b-8c9d-0e1f2a3b4c5d")  # logicalId namespace

NATIVE_ITEMS = ["FabricIqOntology.Ontology", "FabricIqOntologyAgent.DataAgent", "FabricIqDirectAgent.DataAgent"]

DOCS_BODY_TEMPLATE = '''# MARKDOWN ********************

# # FabricIQ Ontology + Data Agent — Getting Started
# 
# **Everything is already deployed and loaded.** The install command deployed the
# Lakehouse, Eventhouse, the **FabricIqOntology** semantic model, and both **Data
# Agents** — and loaded the {industry} sample data. There is nothing to run here.

# MARKDOWN ********************

# ## Prerequisite
# 
# This jumpstart uses **Fabric IQ / Ontology (preview)**. Make sure the preview is **enabled in your tenant**, otherwise the ontology and agents will not work.

# MARKDOWN ********************

# ## What was deployed
# 
# | Item | Type | Purpose |
# |---|---|---|
# | `fabriciq_lakehouse` | Lakehouse | Static business entities (Delta tables) |
# | `fabriciq_eventhouse` | Eventhouse | Time-series / event data (KQL tables) |
# | `FabricIqOntology` | Ontology | The semantic model, bound to the Lakehouse + Eventhouse tables |
# | `FabricIqOntologyAgent` | Data Agent | Answers questions through the ontology |
# | `FabricIqDirectAgent` | Data Agent | Baseline agent over the raw tables |
# 
# The sample data was loaded during install (with event timestamps shifted so the newest land ~yesterday), and the ontology was refreshed so its graph ingested the data.

# MARKDOWN ********************

# ## Ask questions & compare
# 
# Open each Data Agent and ask the **same** question. The Ontology Agent understands entity relationships and time-series context; the Direct Agent typically cannot join the two sources.
# 
# Give the ontology graph a few minutes after install before judging the first answers.
# 
# Run the cell below for direct links to the created items.

# CELL ********************

# Direct links to the created items (resolved from THIS workspace at runtime).
import sempy.fabric as fabric
from IPython.display import Markdown, display

_routes = {{"Ontology": "ontologies", "DataAgent": "aiskills"}}
_ws = fabric.get_workspace_id()
_items = fabric.list_items()
_lines = []
for _n in ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]:
    _m = _items[_items["Display Name"] == _n]
    if len(_m):
        _t = str(_m.iloc[0].Type)
        _route = _routes.get(_t)
        if _route:
            _url = f"https://app.fabric.microsoft.com/groups/{{_ws}}/{{_route}}/{{str(_m.iloc[0].Id)}}"
            _lines.append(f"- [{{_n}}]({{_url}}) ({{_t}})")
        else:
            _lines.append(f"- {{_n}} ({{_t}})")
    else:
        _lines.append(f"- {{_n}} (not found)")
display(Markdown("**Your items:**\\n\\n" + "\\n".join(_lines)))

# METADATA ********************

# META {{
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }}

# MARKDOWN ********************

# ## Next steps
# 
# - Explore the `FabricIqOntology` item and its bindings.
# - Re-run the install with a different `install_option` (in a new workspace) to see another industry.
# - Delete the workspace when you're done to clean up.
'''

PARAM_TEMPLATE = """  # --- native Ontology/DataAgent items: rewire authoring-workspace refs ---
  # (find_values are globally-unique GUIDs/URIs so no item_type filter is needed)
  - find_value: "{ws}" # ontology authoring workspace id
    replace_value:
      _ALL_: "$workspace.$id"
  - find_value: "{lh}" # authoring fabriciq_lakehouse id
    replace_value:
      _ALL_: "$items.Lakehouse.fabriciq_lakehouse.$id"
  - find_value: "{eh}" # authoring fabriciq_eventhouse id
    replace_value:
      _ALL_: "$items.Eventhouse.fabriciq_eventhouse.$id"
  - find_value: "{kdb}" # authoring KQL database id
    replace_value:
      _ALL_: "$items.KQLDatabase.fabriciq_eventhouse.$id"
  - find_value: "{cluster}" # authoring kusto cluster uri
    replace_value:
      _ALL_: "$items.Eventhouse.fabriciq_eventhouse.$queryserviceuri"
  - find_value: "{ont}" # authoring FabricIqOntology item id
    replace_value:
      _ALL_: "$items.Ontology.FabricIqOntology.$id"
"""


def fabric_token() -> str:
    return subprocess.run(
        ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com",
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True, shell=True,
    ).stdout.strip()


def get_definition(h: dict, ws: str, item_id: str) -> dict:
    r = requests.post(f"{FABRIC_API}/workspaces/{ws}/items/{item_id}/getDefinition", headers=h, timeout=60)
    if r.status_code == 202:
        loc = r.headers["Location"]
        for _ in range(60):
            time.sleep(2)
            if requests.get(loc, headers=h, timeout=60).json().get("status") == "Succeeded":
                break
        return requests.get(f"{loc}/result", headers=h, timeout=60).json()
    r.raise_for_status()
    return r.json()


def main(industry: str, author_ws: str) -> None:
    dest = ROOT / industry
    if not dest.exists():
        raise SystemExit(f"option folder not found: {dest}")

    h = {"Authorization": f"Bearer {fabric_token()}", "Content-Type": "application/json"}
    items = requests.get(f"{FABRIC_API}/workspaces/{author_ws}/items", headers=h, timeout=60).json()["value"]
    by = {(i["displayName"], i["type"]): i for i in items}
    lh = by[("fabriciq_lakehouse", "Lakehouse")]
    eh = by[("fabriciq_eventhouse", "Eventhouse")]
    kdb = by[("fabriciq_eventhouse", "KQLDatabase")]
    ont = by[("FabricIqOntology", "Ontology")]
    cluster = requests.get(
        f"{FABRIC_API}/workspaces/{author_ws}/eventhouses/{eh['id']}", headers=h, timeout=60
    ).json()["properties"]["queryServiceUri"]
    print(f"authoring refs: ws={author_ws} lh={lh['id']} eh={eh['id']} kdb={kdb['id']}\n  cluster={cluster} ont={ont['id']}")

    # 1) export + write the three native item folders
    for entry in NATIVE_ITEMS:
        name, _, item_type = entry.partition(".")
        item = by[(name, item_type)]
        d = get_definition(h, author_ws, item["id"])
        folder = dest / entry
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        for part in d["definition"]["parts"]:
            target = folder / part["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = base64.b64decode(part["payload"])
            if part["path"] == ".platform":
                platform = json.loads(payload)
                platform["config"]["logicalId"] = str(uuid.uuid5(NS, f"{industry}/{entry}"))
                target.write_text(json.dumps(platform, indent=2) + "\n", encoding="utf-8")
            else:
                target.write_bytes(payload)
        print(f"written: {folder.relative_to(HERE)} ({len(d['definition']['parts'])} parts)")

    # 2) parameter.yml
    p = dest / "parameter.yml"
    text = p.read_text(encoding="utf-8")
    if "native Ontology/DataAgent" not in text:
        p.write_text(
            text.rstrip() + "\n" + PARAM_TEMPLATE.format(
                ws=author_ws, lh=lh["id"], eh=eh["id"], kdb=kdb["id"], cluster=cluster, ont=ont["id"]
            ),
            encoding="utf-8",
        )
        print("parameter.yml patched")

    # 3) remove runtime notebooks
    for nb in ["01_generate_ontology_data.Notebook", "02_create_ontology.Notebook"]:
        if (dest / nb).exists():
            shutil.rmtree(dest / nb)
            print(f"removed {nb}")

    # 4) docs-only GettingStarted (keep the original header/binding block)
    gs = dest / "GettingStarted.Notebook" / "notebook-content.py"
    src = gs.read_text(encoding="utf-8")
    header = src[: src.index("# MARKDOWN ********************")]
    gs.write_text(header + DOCS_BODY_TEMPLATE.format(industry=industry), encoding="utf-8")
    print("GettingStarted rewritten as docs-only")

    import py_compile

    py_compile.compile(str(gs), doraise=True)
    print(f"\n{industry}: promoted to native one-step layout")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
