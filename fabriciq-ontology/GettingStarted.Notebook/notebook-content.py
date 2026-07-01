# Fabric notebook source


# MARKDOWN ********************

# # FabricIQ Ontology + Data Agent - Getting Started
# 
# This jumpstart builds a semantic **ontology** over a **Lakehouse** (business entities) and an **Eventhouse** (time-series), binds it to real tables, and exposes it through a **Fabric Data Agent** for natural-language, context-aware analytics.
# 
# Follow the three steps below in order.

# MARKDOWN ********************

# ## Prerequisite
# 
# This jumpstart uses **Fabric IQ / Ontology (preview)**. Make sure the preview is **enabled in your tenant** before you begin, otherwise Step 2 (building the ontology) will fail.

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
# The **Ontology** item and the two **Data Agents** are created for you when you run `02_create_ontology` (Step 2).

# CELL ********************

# Resolve dynamic links to the two notebooks you run in this jumpstart.
try:
    import sempy.fabric as fabric
    from IPython.display import display, Markdown
    ws = fabric.get_workspace_id()
    items = fabric.list_items()

    def _link(name):
        m = items[(items['Type'] == 'Notebook') & (items['Display Name'] == name)]
        if len(m) == 0:
            return f'**{name}** (not found yet - deploy may still be finishing)'
        nid = str(m.iloc[0].Id)
        return f'[{name}](https://app.fabric.microsoft.com/groups/{ws}/synapsenotebooks/{nid})'

    display(Markdown(
        '**Run these two notebooks in order:**\n\n'
        f'1. {_link("01_generate_ontology_data")} - load the data\n\n'
        f'2. {_link("02_create_ontology")} - build the ontology + two data agents'
    ))
except Exception as e:
    print('Open this notebook inside your Fabric workspace to get clickable links.')
    print('Then run 01_generate_ontology_data, followed by 02_create_ontology.')
    print('Context unavailable:', e)

# MARKDOWN ********************

# ## Step 1 - Load the data
# 
# Open **`01_generate_ontology_data`** (link above) and **Run all**. It loads the industry sample data into `fabriciq_lakehouse` (Delta tables) and `fabriciq_eventhouse` (KQL tables).

# MARKDOWN ********************

# ## Step 2 - Build the ontology + agents
# 
# Open **`02_create_ontology`** and **Run all**. It builds the semantic ontology, binds it to the Lakehouse + Eventhouse tables, creates the **`FabricIqOntology`** item, and publishes **two Data Agents**:
# 
# - **Ontology Agent** - grounded on the ontology; understands the Lakehouse/Eventhouse relationships.
# - **Direct Agent** - queries the raw tables with no ontology (for comparison).

# MARKDOWN ********************

# ## Step 3 - Ask questions & compare
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
