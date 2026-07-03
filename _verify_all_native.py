"""Verify all 12 industry folders are native one-step and consistent."""
import py_compile
from pathlib import Path

ROOT = Path(__file__).parent / "fabricdemogallery-fabriciq"
INDUSTRIES = ["construction", "education", "energy-grid", "financial-services", "healthcare",
              "hospitality", "manufacturing-qc", "media", "professional-services",
              "retail-sales", "technology", "transportation"]

REQUIRED = ["fabriciq_lakehouse.Lakehouse", "fabriciq_eventhouse.Eventhouse",
            "FabricIqOntology.Ontology", "FabricIqOntologyAgent.DataAgent",
            "FabricIqDirectAgent.DataAgent", "GettingStarted.Notebook", "parameter.yml"]
FORBIDDEN = ["01_generate_ontology_data.Notebook", "02_create_ontology.Notebook"]

logical_ids = {}
ok = True
for ind in INDUSTRIES:
    d = ROOT / ind
    problems = []
    for req in REQUIRED:
        if not (d / req).exists():
            problems.append(f"missing {req}")
    for forb in FORBIDDEN:
        if (d / forb).exists():
            problems.append(f"still has {forb}")
    gs = d / "GettingStarted.Notebook" / "notebook-content.py"
    try:
        py_compile.compile(str(gs), doraise=True)
    except Exception as e:  # noqa: BLE001
        problems.append(f"GettingStarted compile: {e}")
    src = gs.read_text(encoding="utf-8")
    if "notebookutils.notebook.run" in src:
        problems.append("GettingStarted still orchestrates")
    param = (d / "parameter.yml").read_text(encoding="utf-8")
    if param.count("find_value:") != 8:
        problems.append(f"parameter.yml has {param.count('find_value:')} rules (want 8)")
    if "$queryserviceuri" not in param or "$items.Ontology.FabricIqOntology.$id" not in param:
        problems.append("parameter.yml missing dynamic rules")
    # logicalId uniqueness within the folder + capture for cross-check
    import json
    for item in ["FabricIqOntology.Ontology", "FabricIqOntologyAgent.DataAgent", "FabricIqDirectAgent.DataAgent"]:
        plat = json.loads((d / item / ".platform").read_text(encoding="utf-8"))
        lid = plat["config"]["logicalId"]
        if lid == "00000000-0000-0000-0000-000000000000":
            problems.append(f"{item} has null logicalId")
        logical_ids.setdefault(ind, {})[item] = lid
    print(f"{ind:<22} {'OK' if not problems else 'PROBLEMS: ' + '; '.join(problems)}")
    ok = ok and not problems

# per-folder logicalIds must be unique WITHIN a folder (across folders may repeat by design? no - uuid5 per industry => all unique)
all_ids = [lid for per in logical_ids.values() for lid in per.values()]
print("\nlogicalIds unique:", len(all_ids) == len(set(all_ids)), f"({len(all_ids)} total)")
print("ALL GOOD" if ok else "FIX NEEDED")
