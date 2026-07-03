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

# # FabricIQ Ontology + Data Agent — Getting Started
# 
# **Everything is already deployed and loaded.** The install command deployed the
# Lakehouse, Eventhouse, the **FabricIqOntology** semantic model, and both **Data
# Agents** — and loaded the professional-services sample data. There is nothing to run here.

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

_routes = {"Ontology": "ontologies", "DataAgent": "aiskills"}
_ws = fabric.get_workspace_id()
_items = fabric.list_items()
_lines = []
for _n in ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]:
    _m = _items[_items["Display Name"] == _n]
    if len(_m):
        _t = str(_m.iloc[0].Type)
        _route = _routes.get(_t)
        if _route:
            _url = f"https://app.fabric.microsoft.com/groups/{_ws}/{_route}/{str(_m.iloc[0].Id)}"
            _lines.append(f"- [{_n}]({_url}) ({_t})")
        else:
            _lines.append(f"- {_n} ({_t})")
    else:
        _lines.append(f"- {_n} (not found)")
display(Markdown("**Your items:**\n\n" + "\n".join(_lines)))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Next steps
# 
# - Explore the `FabricIqOntology` item and its bindings.
# - Re-run the install with a different `install_option` (in a new workspace) to see another industry.
# - Delete the workspace when you're done to clean up.
