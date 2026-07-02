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
# **Pick your industry below, then press `Run all`** — this notebook runs every step for you.

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
# When you press **Run all**, this notebook runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.

# MARKDOWN ********************

# ## Choose your industry
# 
# Edit `INDUSTRY` in the next cell to theme the whole demo (ontology, sample data, and both Data Agents). Pick one of: `construction`, `education`, `energy-grid`, `financial-services`, `healthcare`, `hospitality`, `manufacturing-qc`, `media`, `professional-services`, `retail-sales`, `technology`, `transportation`.

# CELL ********************

# --- Choose your industry ---
INDUSTRY = "retail-sales"
# Options: construction, education, energy-grid, financial-services, healthcare, hospitality,
#          manufacturing-qc, media, professional-services, retail-sales, technology, transportation

# Fetch the selected industry's ontology package into the lakehouse so 01 + 02 both use it.
import os, urllib.request
_INDUSTRIES = ["construction", "education", "energy-grid", "financial-services", "healthcare",
               "hospitality", "manufacturing-qc", "media", "professional-services",
               "retail-sales", "technology", "transportation"]
assert INDUSTRY in _INDUSTRIES, f"INDUSTRY must be one of: {', '.join(_INDUSTRIES)}"
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/v0.1.5/fabricdemogallery-fabriciq/data"
os.makedirs('/lakehouse/default/Files', exist_ok=True)
_iq_dest = '/lakehouse/default/Files/ontology_package.iq'
urllib.request.urlretrieve(f'{_RAW}/{INDUSTRY}_ontology_package.iq', _iq_dest)
print(f"Selected industry: {INDUSTRY}")
print(f"Ontology package ready at {_iq_dest}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Runs the whole jumpstart for you: loads the data (01), then builds the ontology
# and publishes the two Data Agents (02). Each step is a reference run via
# notebookutils.notebook.run; a large timeout is passed because the default is 90s.
import time
import notebookutils

def _run_step(_name, _timeout=1800):
    print(f"=== Running {_name} ===", flush=True)
    _t0 = time.time()
    _rv = notebookutils.notebook.run(_name, _timeout)
    print(f"--- {_name} finished in {int(time.time() - _t0)}s ---\n", flush=True)
    return _rv

_run_step("01_generate_ontology_data")
_run_step("02_create_ontology")
print("All steps complete — the ontology and the two Data Agents are ready.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Show the items this jumpstart created so you can open them from your workspace.
try:
    import sempy.fabric as fabric
    from IPython.display import display, Markdown
    ws = fabric.get_workspace_id()
    items = fabric.list_items()
    wanted = ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]
    rows = []
    for _n in wanted:
        m = items[items['Display Name'] == _n]
        _t = str(m.iloc[0].Type) if len(m) else "(not found yet)"
        rows.append(f"| `{_n}` | {_t} |")
    display(Markdown(
        "**Created items** — open the two agents and ask each the same question:\n\n"
        "| Item | Type |\n|---|---|\n" + "\n".join(rows) +
        f"\n\n[Open workspace](https://app.fabric.microsoft.com/groups/{ws}/list)"
    ))
except Exception as e:
    print("Open your workspace to find FabricIqOntologyAgent and FabricIqDirectAgent.")
    print("Context unavailable:", e)

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
