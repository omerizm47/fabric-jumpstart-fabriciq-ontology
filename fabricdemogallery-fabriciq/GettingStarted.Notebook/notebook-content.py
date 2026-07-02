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
# **Press `Run all`, then pick your industry from the dropdown and click `Build the demo`.**

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
# Pick an industry below and click **Build the demo** — it runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.

# MARKDOWN ********************

# ## Choose your industry & run
# 
# The dropdown themes the whole demo (ontology, sample data, and both Data Agents) to the industry you pick.

# CELL ********************

# Pick your industry, then click "Build the demo" — it fetches that industry's ontology
# package and runs 01 (data load) then 02 (ontology + two Data Agents) for you.
import os
import time
import urllib.request

import ipywidgets as widgets
import notebookutils
from IPython.display import display

_INDUSTRIES = ["construction", "education", "energy-grid", "financial-services", "healthcare",
               "hospitality", "manufacturing-qc", "media", "professional-services",
               "retail-sales", "technology", "transportation"]
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/v0.1.12/fabricdemogallery-fabriciq/data"

_dd = widgets.Dropdown(options=_INDUSTRIES, value="retail-sales", description="Industry:",
                       layout=widgets.Layout(width="320px"))
_btn = widgets.Button(description="Build the demo", button_style="success", icon="play")
_out = widgets.Output()

def _run_step(_name, _timeout=1800):
    print(f"=== Running {_name} ===", flush=True)
    _t0 = time.time()
    notebookutils.notebook.run(_name, _timeout)
    print(f"--- {_name} finished in {int(time.time() - _t0)}s ---\n", flush=True)

def _list_created():
    import sempy.fabric as fabric
    items = fabric.list_items()
    for _n in ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]:
        m = items[items["Display Name"] == _n]
        print(f"  {_n}: {str(m.iloc[0].Type) if len(m) else '(not found)'}")

def _go(_):
    _btn.disabled = True
    _dd.disabled = True
    with _out:
        try:
            print(f"Selected industry: {_dd.value}")
            os.makedirs("/lakehouse/default/Files", exist_ok=True)
            urllib.request.urlretrieve(f"{_RAW}/{_dd.value}_ontology_package.iq",
                                       "/lakehouse/default/Files/ontology_package.iq")
            print("Ontology package ready.\n")
            _run_step("01_generate_ontology_data")
            _run_step("02_create_ontology")
            print("All steps complete — created items:")
            _list_created()
            print("\nNOTE: the ontology's graph hydrates asynchronously — give it ~10-15 minutes")
            print("before asking the agents; early answers may be incomplete or empty.")
            print("Open the two Data Agents from your workspace and ask each the same question.")
        except Exception as _e:  # noqa: BLE001
            print(f"FAILED: {_e}")
            _btn.disabled = False
            _dd.disabled = False
            raise

_btn.on_click(_go)
display(widgets.VBox([widgets.HBox([_dd, _btn]), _out]))
print("Pick an industry, then click 'Build the demo'.")

# MARKDOWN ********************

# ## Ask questions & compare
# 
# > **Give the ontology ~10–15 minutes after the build finishes** — its graph model hydrates from the bound tables asynchronously, so the Ontology Agent's first answers may be incomplete until hydration completes.
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
