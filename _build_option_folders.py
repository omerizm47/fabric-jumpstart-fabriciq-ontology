"""Generate per-industry install-option folders (new install_options layout).

Layout produced (repo tag v0.2.0):
    fabricdemogallery-fabriciq/
        jumpstart.yml            (registry mirror)
        data/                    (shared .iq packages + wheel, fetched via raw URLs)
        <industry>/              (one COMPLETE fabric-cicd source per install option)
            parameter.yml
            fabriciq_lakehouse.Lakehouse/
            fabriciq_eventhouse.Eventhouse/   (incl. .children KQLDatabase)
            01_generate_ontology_data.Notebook/
            02_create_ontology.Notebook/
            GettingStarted.Notebook/          (industry FIXED - no dropdown)

The per-industry GettingStarted is generated from the original dropdown version:
the interactive widget cell is replaced by a linear run (fetch package -> run 01
-> run 02 -> list created items).

Run:  python _build_option_folders.py
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE / "fabricdemogallery-fabriciq"
OLD_TAG = "v0.1.15"
NEW_TAG = "v0.2.0"

INDUSTRIES = [
    "construction", "education", "energy-grid", "financial-services", "healthcare",
    "hospitality", "manufacturing-qc", "media", "professional-services",
    "retail-sales", "technology", "transportation",
]

COPY_ITEMS = [
    "parameter.yml",
    "fabriciq_lakehouse.Lakehouse",
    "fabriciq_eventhouse.Eventhouse",
    "01_generate_ontology_data.Notebook",
    "02_create_ontology.Notebook",
]

GS = "GettingStarted.Notebook"

FIXED_CELL_TEMPLATE = '''# This install option builds the {industry} demo end-to-end: it fetches the
# {industry} ontology package and runs 01 (data load) then 02 (ontology + two Data Agents).
import os
import time
import urllib.request

import notebookutils

INDUSTRY = "{industry}"
_RAW = "https://raw.githubusercontent.com/omerizm47/fabric-jumpstart-fabriciq-ontology/{tag}/fabricdemogallery-fabriciq/data"

def _run_step(_name, _timeout=1800):
    print(f"=== Running {{_name}} ===", flush=True)
    _t0 = time.time()
    notebookutils.notebook.run(_name, _timeout)
    print(f"--- {{_name}} finished in {{int(time.time() - _t0)}}s ---\\n", flush=True)

def _list_created():
    # Dynamic links to the created items (per jumpstart standards): resolve item
    # ids from THIS workspace at runtime and render clickable Fabric URLs.
    import sempy.fabric as fabric
    from IPython.display import Markdown, display
    _routes = {{"Ontology": "ontologies", "DataAgent": "aiskills"}}
    _ws = fabric.get_workspace_id()
    items = fabric.list_items()
    _lines = []
    for _n in ["FabricIqOntology", "FabricIqOntologyAgent", "FabricIqDirectAgent"]:
        m = items[items["Display Name"] == _n]
        if len(m):
            _t = str(m.iloc[0].Type)
            _route = _routes.get(_t)
            if _route:
                _url = f"https://app.fabric.microsoft.com/groups/{{_ws}}/{{_route}}/{{str(m.iloc[0].Id)}}"
                _lines.append(f"- [{{_n}}]({{_url}}) ({{_t}})")
            else:
                _lines.append(f"- {{_n}} ({{_t}})")
        else:
            _lines.append(f"- {{_n}} (not found)")
    display(Markdown("**Created items** — open the two Data Agents and ask each the same question:\\n\\n" + "\\n".join(_lines)))

print(f"Industry: {{INDUSTRY}}")
os.makedirs("/lakehouse/default/Files", exist_ok=True)
urllib.request.urlretrieve(f"{{_RAW}}/{{INDUSTRY}}_ontology_package.iq",
                           "/lakehouse/default/Files/ontology_package.iq")
print("Ontology package ready.\\n")
_run_step("01_generate_ontology_data")
_run_step("02_create_ontology")
print("All steps complete.")
_list_created()'''


def build_fixed_gettingstarted(src: str, industry: str) -> str:
    """Transform the dropdown GettingStarted into a fixed-industry one."""
    out = src

    # Intro line
    out = out.replace(
        "# **Press `Run all`, then pick your industry from the dropdown and click `Build the demo`.**",
        f"# **Press `Run all` — this builds the **{industry}** demo end-to-end (data load → ontology → two Data Agents).**",
    )
    # "What was deployed" trailing sentence
    out = out.replace(
        "# Pick an industry below and click **Build the demo** — it runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.",
        "# Pressing **Run all** runs `01_generate_ontology_data` then `02_create_ontology` for you, and the **Ontology** + the two **Data Agents** are created automatically.",
    )
    # Section heading + blurb
    out = out.replace(
        "# ## Choose your industry & run\n# \n# The dropdown themes the whole demo (ontology, sample data, and both Data Agents) to the industry you pick.",
        f"# ## Build the demo\n# \n# This install option themes the whole demo (ontology, sample data, and both Data Agents) to **{industry}**.",
    )

    # Replace the interactive widget cell body with the linear version.
    cell_re = re.compile(
        r"# Pick your industry, then click \"Build the demo\".*?print\(\"Pick an industry, then click 'Build the demo'\.\"\)",
        re.DOTALL,
    )
    if not cell_re.search(out):
        raise RuntimeError("widget cell anchor not found in GettingStarted source")
    fixed_cell = FIXED_CELL_TEMPLATE.format(industry=industry, tag=NEW_TAG)
    out = cell_re.sub(lambda _m: fixed_cell, out)
    return out


def main() -> None:
    gs_src = (ROOT / GS / "notebook-content.py").read_text(encoding="utf-8")
    gs_platform = (ROOT / GS / ".platform").read_text(encoding="utf-8")

    for industry in INDUSTRIES:
        dest = ROOT / industry
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)

        # 1) copy shared items, retagging notebook raw-URL pins
        for name in COPY_ITEMS:
            src_path = ROOT / name
            dst_path = dest / name
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        for nb in ["01_generate_ontology_data.Notebook", "02_create_ontology.Notebook"]:
            p = dest / nb / "notebook-content.py"
            p.write_text(p.read_text(encoding="utf-8").replace(OLD_TAG, NEW_TAG), encoding="utf-8")

        # 2) generate the fixed-industry GettingStarted
        gs_dir = dest / GS
        gs_dir.mkdir()
        (gs_dir / ".platform").write_text(gs_platform, encoding="utf-8")
        (gs_dir / "notebook-content.py").write_text(
            build_fixed_gettingstarted(gs_src, industry), encoding="utf-8"
        )
        print(f"built option folder: {industry}")

    print("done.")


if __name__ == "__main__":
    main()
