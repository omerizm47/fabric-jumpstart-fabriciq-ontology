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

# # Fabric IQ — Create Ontology from Package
# Builds the ontology definition from the `.iq` package in the lakehouse `Files/`, binds its
# entities to the lakehouse (static) and eventhouse (time-series) tables created by the previous
# notebook, and creates the **Ontology** item in this workspace.

# CELL ********************

# --- Jumpstart auto-config: resolve everything from THIS workspace at runtime ---
# Replaces the templated placeholders the gallery backend used to inject.
# NOTE: verify the Eventhouse REST path + sempy calls during the first live run.
import glob
import sempy.fabric as _fab
from sempy.fabric import FabricRestClient as _FRC

LAKEHOUSE_NAME = "fabriciq_lakehouse"
EVENTHOUSE_NAME = "fabriciq_eventhouse"

# Ensure the accelerator wheel + ontology package are in the lakehouse Files area.
# On a clean install they are not uploaded, so fetch them from the pinned repo.
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/v0.1.11/fabricdemogallery-fabriciq/data"

# Industry package. In the normal flow GettingStarted pre-places the chosen package as
# Files/ontology_package.iq; set INDUSTRY here only if you run this notebook standalone.
INDUSTRY = "retail-sales"
# Options: construction, education, energy-grid, financial-services, healthcare, hospitality,
#          manufacturing-qc, media, professional-services, retail-sales, technology, transportation

def _ensure(_pattern, _fname):
    _hits = sorted(glob.glob(f'/lakehouse/default/Files/**/{_pattern}', recursive=True))
    if _hits:
        return _hits[0]
    import os, urllib.request
    os.makedirs('/lakehouse/default/Files', exist_ok=True)
    _dest = f'/lakehouse/default/Files/{_fname}'
    urllib.request.urlretrieve(f'{_RAW}/{_fname}', _dest)
    print(f'Downloaded {_fname} from the jumpstart repo')
    return _dest

def _ensure_iq():
    import os, urllib.request
    _fixed = '/lakehouse/default/Files/ontology_package.iq'
    if os.path.exists(_fixed):
        return _fixed  # placed by GettingStarted (the chosen industry)
    os.makedirs('/lakehouse/default/Files', exist_ok=True)
    urllib.request.urlretrieve(f'{_RAW}/{INDUSTRY}_ontology_package.iq', _fixed)
    print(f'Downloaded {INDUSTRY} ontology package')
    return _fixed

_JS_WHL = _ensure('*.whl', 'fabriciq_ontology_accelerator-0.1.0-py3-none-any.whl')
_JS_IQ = _ensure_iq()

_ws = _fab.get_workspace_id()
_items = _fab.list_items()
_eh = _items[(_items['Type'] == 'Eventhouse') & (_items['Display Name'] == EVENTHOUSE_NAME)]
assert len(_eh) > 0, f'Eventhouse {EVENTHOUSE_NAME!r} not found in this workspace.'
_JS_EH_URI = _FRC().get(f"/v1/workspaces/{_ws}/eventhouses/{str(_eh.iloc[0].Id)}").json()['properties']['queryServiceUri']

def _kusto_real_db_name(_uri, _pretty):
    """Resolve the Kusto-level DatabaseName (API-created DBs get a GUID name;
    the display name is only the PrettyName)."""
    import json as _j
    import urllib.request as _ur
    from notebookutils import mssparkutils as _msu
    _tok = _msu.credentials.getToken(_uri)
    _req = _ur.Request(
        f"{_uri}/v1/rest/mgmt",
        data=_j.dumps({"csl": ".show databases | project DatabaseName, PrettyName"}).encode(),
        headers={"Authorization": f"Bearer {_tok}", "Content-Type": "application/json"},
    )
    _rows = _j.loads(_ur.urlopen(_req, timeout=30).read())["Tables"][0]["Rows"]
    for _dbn, _pn in _rows:
        if _pretty in (_dbn, _pn):
            return _dbn
    return None

_JS_EH_DB = _kusto_real_db_name(_JS_EH_URI, EVENTHOUSE_NAME)
assert _JS_EH_DB, f'KQL database for {EVENTHOUSE_NAME!r} not found - run 01_generate_ontology_data first.'

print('Jumpstart config resolved:')
print('  whl:', _JS_WHL)
print('  iq :', _JS_IQ)
print('  eh :', _JS_EH_URI)
print('  db :', _JS_EH_DB)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Install the Fabric IQ Ontology Accelerator package (uploaded to the lakehouse Files/).
# Use a subprocess pip install instead of the `%pip` magic: `%pip` restarts the kernel
# and is unreliable in job-mode (deployer-triggered) runs — that surfaces as
# System_Cancelled_Session_Statements_Failed. subprocess installs in-place without
# tearing down the live Spark session.
import subprocess, sys
_whl = _JS_WHL
print(f"Installing {_whl} ...")
_p = subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", _whl],
                    capture_output=True, text=True)
print((_p.stdout or "")[-2000:])
if _p.returncode != 0:
    print((_p.stderr or "")[-3000:])
    raise RuntimeError(f"pip install failed (exit {_p.returncode}) — see stderr above")
print("Accelerator library installed.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import sempy.fabric as fabric
from fabricontology import create_ontology_item, generate_definition_from_package

ONTOLOGY_PACKAGE_PATH = _JS_IQ
ONTOLOGY_ITEM_NAME    = "FabricIqOntology"

BINDING_LAKEHOUSE_NAME        = "fabriciq_lakehouse"
BINDING_LAKEHOUSE_SCHEMA_NAME = "dbo"
BINDING_EVENTHOUSE_NAME       = "fabriciq_eventhouse"
BINDING_EVENTHOUSE_CLUSTER_URI = _JS_EH_URI
# Display name, not the GUID DatabaseName: Kusto resolves it, and downstream
# consumers inline it into KQL where a GUID is an invalid identifier.
BINDING_EVENTHOUSE_DATABASE_NAME = "fabriciq_eventhouse"

workspace_id = fabric.get_workspace_id()
access_token = notebookutils.credentials.getToken('pbi')
print(f"Workspace: {workspace_id}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Resolve the lakehouse + eventhouse item ids the ontology binds to.
items_df = fabric.list_items()
binding_lakehouse_item_id = str(
    items_df[(items_df["Type"] == "Lakehouse") & (items_df["Display Name"] == BINDING_LAKEHOUSE_NAME)].iloc[0].Id
)
binding_eventhouse_item_id = str(
    items_df[(items_df["Type"] == "Eventhouse") & (items_df["Display Name"] == BINDING_EVENTHOUSE_NAME)].iloc[0].Id
)
print(f"Lakehouse item id : {binding_lakehouse_item_id}")
print(f"Eventhouse item id: {binding_eventhouse_item_id}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Build the ontology definition with data bindings resolved to this workspace's items.
ontology_definition, entity_types, relationship_types, data_bindings, contextualizations = generate_definition_from_package(
    ontology_package_path=ONTOLOGY_PACKAGE_PATH,
    ontology_name=ONTOLOGY_ITEM_NAME,
    binding_workspace_id=workspace_id,
    binding_lakehouse_item_id=binding_lakehouse_item_id,
    binding_lakehouse_schema_name=BINDING_LAKEHOUSE_SCHEMA_NAME,
    binding_eventhouse_item_id=binding_eventhouse_item_id,
    binding_eventhouse_cluster_uri=BINDING_EVENTHOUSE_CLUSTER_URI,
    binding_eventhouse_database_name=BINDING_EVENTHOUSE_DATABASE_NAME,
)
print(f"Entity types        : {len(entity_types)}")
print(f"Relationship types  : {len(relationship_types)}")
print(f"Data bindings       : {len(data_bindings)}")
print(f"Contextualizations  : {len(contextualizations)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create the Ontology item in the workspace.
response = create_ontology_item(
    workspace_id=workspace_id,
    access_token=access_token,
    ontology_item_name=ONTOLOGY_ITEM_NAME,
    ontology_definition=ontology_definition,
)
try:
    print(response.json())
except Exception:
    print(response)
print(f"\nOntology '{ONTOLOGY_ITEM_NAME}' created and bound to lakehouse + eventhouse.")

# Resolve the new Ontology item id (used as the data agent's data source).
# Prefer the id from the create response (most reliable); fall back to listing items.
import time as _t
ontology_item_id = None

# 1) Try to read the id straight from the create-operation result.
try:
    _body = response.json() if hasattr(response, "json") else (response or {})
    if isinstance(_body, dict):
        ontology_item_id = _body.get("id") or (_body.get("definition", {}) or {}).get("id")
except Exception:
    pass

# 2) Fall back to listing items. The Ontology item is the EXACT-name match — its
#    backing artifacts are suffixed ('<name>_graph', '<name>_lh'), so match the
#    exact display name and Type == 'Ontology'. Poll a while: the item + its
#    backing graph/lakehouse provision asynchronously.
if not ontology_item_id:
    for _ in range(40):
        items_df2 = fabric.list_items()
        match = items_df2[(items_df2["Type"] == "Ontology") & (items_df2["Display Name"] == ONTOLOGY_ITEM_NAME)]
        if len(match) > 0:
            ontology_item_id = str(match.iloc[0].Id)
            break
        _t.sleep(5)

print(f"Ontology item id: {ontology_item_id}")
if not ontology_item_id:
    print("WARNING: could not resolve the Ontology item id — the data agent step will be skipped.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Create two Data Agents (ontology vs. raw tables)
# Builds **two** Fabric data agents so you can compare answer quality:
# 
# 1. **Ontology agent** — grounded on the ontology's graph model (`graph` data source). It answers in
#    business terms (entities + relationships), so multi-hop / join questions resolve through the
#    ontology's context.
# 2. **Direct agent** — grounded on the raw **Lakehouse tables** (`lakehouse_tables`) + **Eventhouse**
#    (`kusto`) with no semantic layer, the baseline.
# 
# Both are created + published through the AISkill workload API (the same REST sequence the
# `fabric-data-agent-sdk` uses). Outcomes are written to `Files/data_agent_result.json` so the
# deployer can read them back. Best-effort: any preview-API hiccup is captured in the result file.


# CELL ********************

import json, time, uuid
import synapse.ml.fabric.service_discovery as sd
from sempy.fabric.exceptions import FabricHTTPException

ONTOLOGY_AGENT_NAME = "FabricIqOntologyAgent"
DIRECT_AGENT_NAME   = "FabricIqDirectAgent"
AGENT_DOMAIN        = "operations"   # e.g. "retail operations"

ONTOLOGY_INSTRUCTIONS = (
    f"You answer questions about {AGENT_DOMAIN} using the ontology's business "
    "entities and the relationships between them. Traverse relationships to join "
    "across entities instead of guessing key columns. Support group by in GQL."
)
DIRECT_INSTRUCTIONS = (
    f"You answer questions about {AGENT_DOMAIN} by querying the lakehouse tables and "
    "the eventhouse (KQL) tables directly. Join tables on their shared id columns."
)

# ── Resolve the artifact ids the two agents bind to ──────────────────────────
_items = fabric.list_items()


def _find(type_contains, name_exact=None, name_prefix=None):
    for _, row in _items.iterrows():
        t = str(row.get("Type", "")).lower()
        n = str(row.get("Display Name", ""))
        if type_contains in t and (name_exact is None or n == name_exact) and (name_prefix is None or n.startswith(name_prefix)):
            return str(row["Id"]), n
    return None, None


# The ontology's queryable surface is its backing Graph model item ("<name>_graph_…").
graph_item_id, graph_item_name = _find("graph", name_prefix=ONTOLOGY_ITEM_NAME)
# The eventhouse auto-creates a default KQL database with the same display name.
kqldb_item_id, kqldb_item_name = _find("kqldatabase", name_exact=BINDING_EVENTHOUSE_NAME)
lakehouse_id = binding_lakehouse_item_id

print(f"Ontology item id : {ontology_item_id}")
print(f"Graph model id   : {graph_item_id} ({graph_item_name})")
print(f"Lakehouse id     : {lakehouse_id}")
print(f"KQL database id  : {kqldb_item_id} ({kqldb_item_name})")

client = fabric.FabricRestClient()
ws = fabric.get_workspace_id()
host = sd.get_fabric_env_config().fabric_env_config.wl_host
cap = client.get(f"v1/workspaces/{ws}").json().get("capacityId")


def _select_all(elements):
    for e in elements or []:
        # Select every table/entity/column node so the whole source is queryable.
        e["is_selected"] = True
        _select_all(e.get("children"))


def build_and_publish_agent(da_name, sources, instructions):
    """Create + publish one data agent over ``sources`` (a list of
    ``{"artifact_id", "ds_type", "extra_qs"}``) via the AISkill workload API.
    Returns a result dict (best-effort; errors captured, never raised)."""
    res = {"agent": da_name, "status": "error", "step": "start", "sources": []}
    try:
        # 1. Create the data agent item, resolve its id by name.
        res["step"] = "create"
        try:
            client.post(f"v1/workspaces/{ws}/dataagents", json={"artifactType": "LLMPlugin", "displayName": da_name})
        except FabricHTTPException as ce:
            # Fabric Data Agents are NOT available on Trial (FT1) capacity — the
            # API returns 400 UnsupportedCapacitySKU. Surface a clear, non-fatal
            # status so the deploy still succeeds (ontology + tables are intact).
            body = ""
            try:
                body = ce.response.text
            except Exception:
                body = str(ce)
            if "UnsupportedCapacitySKU" in body or "SKU Not Supported" in body:
                res["status"] = "unsupported_sku"
                res["error"] = "Data agents require a paid Fabric capacity (F2+ with Copilot/AI). This workspace is on a Trial/unsupported SKU (e.g. FT1), so the agent was skipped. Re-deploy on a paid F-SKU to auto-create it."
                return res
            raise
        da_id = None
        for _ in range(20):
            agents = client.get(f"v1/workspaces/{ws}/items?type=DataAgent").json().get("value", [])
            m = [i for i in agents if i.get("displayName") == da_name]
            if m:
                da_id = m[0]["id"]; break
            time.sleep(3)
        if not da_id:
            raise RuntimeError("data agent item did not appear after create")
        res["dataAgentId"] = da_id

        moniker = str(uuid.uuid4())
        H = {"x-ms-workload-resource-moniker": moniker, "x-ms-ai-assistant-scenario": "data_agent", "x-ms-ai-aiskill-stage": "sandbox"}
        base = f"{host}/webapi/capacities/{cap}/workloads/ML/AISkill/Automatic/workspaces/{ws}/dataagents/{da_id}"

        # 2. Add each data source. ``sources`` is a list of source-groups; each
        #    group is a list of CANDIDATES (ds_type + artifact_id) tried in order
        #    on the SAME agent item until one attaches (so we never recreate the
        #    agent just to fall back on a datasource type).
        for group in sources:
            candidates = group if isinstance(group, list) else [group]
            g_out = {"tried": [], "ok": False}
            for cand in candidates:
                attempt = {"ds_type": cand["ds_type"], "artifact_id": cand["artifact_id"]}
                try:
                    res["step"] = f"schema:{cand['ds_type']}"
                    schema_url = (f"{host}/webapi/capacities/{cap}/workloads/ML/AISkill/Automatic/v1/workspaces/{ws}"
                                  f"/artifacts/{cand['artifact_id']}/schema?responseSource=live&dataSourceType={cand['ds_type']}"
                                  + cand.get("extra_qs", ""))
                    sch = client.get(schema_url, headers={"x-ms-upstream-artifact-id": da_id, "x-ms-workload-resource-moniker": moniker}).json()
                    res["step"] = f"add:{cand['ds_type']}"
                    ds_id = client.post(f"{base}/management/datasources", json=sch["schema"], headers=H).json()["id"]
                    dr = client.get(f"{base}/management/datasources/{ds_id}")
                    cfg = dr.json()
                    _select_all(cfg.get("elements", []))
                    client.put(f"{base}/management/datasources/{ds_id}", json=cfg, headers={**H, "If-Match": dr.headers.get("ETag")})
                    g_out["ok"] = True
                    g_out["ds_type"] = cand["ds_type"]
                    g_out["artifact_id"] = cand["artifact_id"]
                    g_out["datasourceId"] = ds_id
                    break
                except Exception as se:  # noqa: BLE001 — try next candidate
                    attempt["error"] = f"{type(se).__name__}: {se}"
                    g_out["tried"].append(attempt)
            res["sources"].append(g_out)

        if not any(s.get("ok") for s in res["sources"]):
            errs = []
            for s in res["sources"]:
                for t in s.get("tried", []):
                    errs.append(f"{t['ds_type']}: {t.get('error','')[:120]}")
            raise RuntimeError("no data source could be added — " + "; ".join(errs))

        # 3. Instructions.
        res["step"] = "instructions"
        cr = client.get(f"{base}/management/configuration")
        ccfg = cr.json(); ccfg["additionalInstructions"] = instructions; ccfg.pop("dataSources", None)
        client.patch(f"{base}/management/configuration", json=ccfg, headers={**H, "If-Match": cr.headers.get("ETag")})

        # 4. Publish info (GET may 404 for a fresh agent → create with empty If-Match).
        res["step"] = "publish_info"
        try:
            pr = client.get(f"{base}/management/publishing")
            pinfo = pr.json(); pinfo["description"] = da_name; petag = pr.headers.get("ETag", "")
        except FabricHTTPException as pe:
            if getattr(pe, "status_code", None) != 404:
                raise
            pinfo = {"description": da_name}; petag = ""
        client.put(f"{base}/management/publishing", json=pinfo, headers={"Content-Type": "application/json", "If-Match": petag})

        # 5. Deploy (publish).
        res["step"] = "deploy"
        cr = client.get(f"{base}/management/configuration")
        dep = client.put(f"{base}/management/deploy", headers={"Content-Type": "application/json", "If-Match": cr.headers.get("ETag")})
        res["deployStatus"] = dep.status_code
        res["status"] = "published"
        res["step"] = "done"
    except Exception as e:  # noqa: BLE001
        import traceback
        res["error"] = f"{type(e).__name__}: {e}"
        res["trace"] = traceback.format_exc()[-1200:]
    return res


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# ── Agent A: grounded on the ontology ────────────────────────────────────────
# One source with candidate fallbacks tried on the same agent item:
#   1. ontology item id, dataSourceType=ontology  (proven on retail)
#   2. ontology item id, dataSourceType=graph
#   3. backing graph-model item, dataSourceType=graph
ontology_candidates = []
if ontology_item_id:
    ontology_candidates.append({"artifact_id": ontology_item_id, "ds_type": "ontology", "extra_qs": ""})
    ontology_candidates.append({"artifact_id": ontology_item_id, "ds_type": "graph", "extra_qs": ""})
if graph_item_id:
    ontology_candidates.append({"artifact_id": graph_item_id, "ds_type": "graph", "extra_qs": ""})

agent_a = build_and_publish_agent(ONTOLOGY_AGENT_NAME, [ontology_candidates], ONTOLOGY_INSTRUCTIONS) \
    if ontology_candidates else {"agent": ONTOLOGY_AGENT_NAME, "status": "skipped", "error": "no ontology artifact resolved"}

# ── Agent B: grounded on the raw lakehouse + eventhouse (no ontology) ─────────
direct_sources = []
if lakehouse_id:
    direct_sources.append([{"artifact_id": lakehouse_id, "ds_type": "lakehouse_tables", "extra_qs": ""}])
if kqldb_item_id:
    direct_sources.append([{"artifact_id": kqldb_item_id, "ds_type": "kusto", "extra_qs": ""}])

agent_b = build_and_publish_agent(DIRECT_AGENT_NAME, direct_sources, DIRECT_INSTRUCTIONS) \
    if direct_sources else {"agent": DIRECT_AGENT_NAME, "status": "skipped", "error": "no lakehouse/eventhouse artifact resolved"}

result = {
    "ontologyAgent": agent_a,
    "directAgent": agent_b,
    "resolved": {
        "ontologyItemId": ontology_item_id,
        "graphItemId": graph_item_id,
        "lakehouseId": lakehouse_id,
        "kqlDatabaseId": kqldb_item_id,
    },
}
try:
    with open("/lakehouse/default/Files/data_agent_result.json", "w") as f:
        json.dump(result, f)
except Exception as fe:  # noqa: BLE001
    result["writeError"] = str(fe)

print(json.dumps(result, indent=2))
notebookutils.notebook.exit(json.dumps(result))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
