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

# # Fabric IQ — Generate Ontology Data
# Loads the ontology package's instance data into the **lakehouse** (Delta tables) and its
# time-series data into the **eventhouse** (Kusto tables), using the Fabric IQ accelerator library.
# The `.whl` and `.iq` files are fetched into `Files/` at runtime from the jumpstart repo (see the config cell).

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
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/v0.1.3/fabriciq-ontology/data"

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
print('Jumpstart config resolved:')
print('  whl:', _JS_WHL)
print('  iq :', _JS_IQ)
print('  eh :', _JS_EH_URI)


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

from fabricontology.generate_data import generate_instance_data, generate_events_data
from notebookutils import mssparkutils

ONTOLOGY_PACKAGE_PATH = _JS_IQ
LAKEHOUSE_SCHEMA      = "dbo"
EVENTHOUSE_CLUSTER_URI = _JS_EH_URI
EVENTHOUSE_DATABASE    = "fabriciq_eventhouse"

print(f"Package : {ONTOLOGY_PACKAGE_PATH}")
print(f"Lakehouse schema : {LAKEHOUSE_SCHEMA}")
print(f"Eventhouse : {EVENTHOUSE_CLUSTER_URI} / {EVENTHOUSE_DATABASE}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create the instance (static) Delta tables in the default lakehouse.
instance_result = generate_instance_data(
    spark,
    ontology_package_path=ONTOLOGY_PACKAGE_PATH,
    database=LAKEHOUSE_SCHEMA,
    mode="overwrite",
)
print("Lakehouse tables created:")
for k, v in (instance_result or {}).items():
    print(f"  {k} -> {v}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create the time-series Kusto tables in the eventhouse (best-effort).
# A freshly-created Eventhouse can take a short while before its default KQL
# database accepts writes; retry a few times. A persistent Kusto hiccup must NOT
# cancel the whole session — the lakehouse tables + ontology can still proceed,
# so we capture the outcome instead of raising.
import json as _json, time as _time
from notebookutils import mssparkutils

events_result = {}
events_error = ""
for _attempt in range(4):
    try:
        access_token = mssparkutils.credentials.getToken(EVENTHOUSE_CLUSTER_URI)
        events_result = generate_events_data(
            spark,
            ontology_package_path=ONTOLOGY_PACKAGE_PATH,
            eventhouse_cluster_uri=EVENTHOUSE_CLUSTER_URI,
            eventhouse_database=EVENTHOUSE_DATABASE,
            access_token=access_token,
        )
        events_error = ""
        break
    except Exception as _e:  # noqa: BLE001
        events_error = f"{type(_e).__name__}: {_e}"
        print(f"Eventhouse write attempt {_attempt + 1}/4 failed: {events_error[:300]}")
        _time.sleep(20)

print("Eventhouse tables created:" if events_result else "Eventhouse tables NOT created.")
for k, v in (events_result or {}).items():
    print(f"  {k} -> {v}")

# Record the outcome so the deployer can read it back.
_summary = {
    "lakehouseTables": list((instance_result or {}).values()),
    "eventhouseTables": list((events_result or {}).values()),
    "eventhouseError": events_error,
}
try:
    with open("/lakehouse/default/Files/load_data_result.json", "w") as _f:
        _json.dump(_summary, _f)
except Exception as _fe:  # noqa: BLE001
    print(f"Could not write load_data_result.json: {_fe}")

print("\nData load complete (lakehouse always; eventhouse best-effort).")
print(_json.dumps(_summary, indent=2))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
