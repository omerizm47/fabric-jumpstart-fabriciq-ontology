# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "b5ae6e8b-5726-489e-9cf1-17c3416393d6",
# META       "default_lakehouse_name": "fabriciq_lakehouse",
# META       "default_lakehouse_workspace_id": "a537bf46-7b26-4ed7-b48d-dbccd64a29cc",
# META       "known_lakehouses": [
# META         {
# META           "id": "b5ae6e8b-5726-489e-9cf1-17c3416393d6"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # FabricIQ Ontology + Data Agent - Getting Started
# 
# This jumpstart builds a semantic **ontology** over a **Lakehouse** (business entities) and an **Eventhouse** (time-series), binds it to real tables, and exposes it through a **Fabric Data Agent** for natural-language, context-aware analytics.
# 
# **Press `Run all` — this builds the **healthcare** demo end-to-end (data load → ontology → two Data Agents).**

# MARKDOWN ********************

# ## Prerequisite
# 
# This jumpstart uses **Fabric IQ / Ontology (preview)**. Make sure the preview is **enabled in your tenant** before you run this, otherwise building the ontology will fail.

# MARKDOWN ********************

# ## What was deployed
# 
# | Item | Type | Purpose |
# |---|---|---|
# | `fabriciq_lakehouse` | Lakehouse | Static business entities (Delta tables) |
# | `fabriciq_eventhouse` | Eventhouse | Time-series / event data (KQL tables) |
# | `01_generate_ontology_data` | Notebook | Loads sample data into the Lakehouse + Eventhouse |
# | `02_create_ontology` | Notebook | Builds the ontology, binds it, and creates two Data Agents |
# 
# Pressing **Run all** runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.

# MARKDOWN ********************

# ## Build the demo
# 
# This install option themes the whole demo (ontology, sample data, and both Data Agents) to **healthcare**.

# CELL ********************

# This install option builds the healthcare demo end-to-end: it fetches the
# healthcare ontology package and runs 01 (data load) then 02 (ontology + two Data Agents).
import os
import time
import urllib.request

import notebookutils

INDUSTRY = "healthcare"
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/v0.2.0/fabricdemogallery-fabriciq/data"

def _run_step(_name, _timeout=1800):
    print(f"=== Running {_name} ===", flush=True)
    _t0 = time.time()
    notebookutils.notebook.run(_name, _timeout)
    print(f"--- {_name} finished in {int(time.time() - _t0)}s ---\n", flush=True)

def _list_created():
    # Dynamic links to the created items (per jumpstart standards): resolve item
    # ids from THIS workspace at runtime and render clickable Fabric URLs.
    import sempy.fabric as fabric
    from IPython.display import Markdown, display
    _routes = {"Ontology": "ontologies", "DataAgent": "aiskills"}
    _ws = fabric.get_workspace_id()
    items = fabric.list_items()
    _lines = []
    for _n in ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]:
        m = items[items["Display Name"] == _n]
        if len(m):
            _t = str(m.iloc[0].Type)
            _route = _routes.get(_t)
            if _route:
                _url = f"https://app.fabric.microsoft.com/groups/{_ws}/{_route}/{str(m.iloc[0].Id)}"
                _lines.append(f"- [{_n}]({_url}) ({_t})")
            else:
                _lines.append(f"- {_n} ({_t})")
        else:
            _lines.append(f"- {_n} (not found)")
    display(Markdown("**Created items** — open the two Data Agents and ask each the same question:\n\n" + "\n".join(_lines)))

print(f"Industry: {INDUSTRY}")
os.makedirs("/lakehouse/default/Files", exist_ok=True)
urllib.request.urlretrieve(f"{_RAW}/{INDUSTRY}_ontology_package.iq",
                           "/lakehouse/default/Files/ontology_package.iq")
print("Ontology package ready.\n")
_run_step("01_generate_ontology_data")
_run_step("02_create_ontology")
print("All steps complete.")
_list_created()

# MARKDOWN ********************

# ## Ask questions & compare
# 
# Open each Data Agent and ask the **same** question. The Ontology Agent understands entity relationships and time-series context and answers correctly; the Direct Agent typically cannot join the two sources.
# 
# Try a question that spans a Lakehouse attribute and an Eventhouse time-series - the exact wording depends on the industry ontology you deployed.

# MARKDOWN ********************

# ## Next steps
# 
# - Explore the `FabricIqOntology` item and its bindings.
# - Re-theme the demo by swapping in another industry's ontology package (`.iq`).
# - Delete the workspace when you're done to clean up.
