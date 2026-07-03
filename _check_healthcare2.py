import py_compile
from pathlib import Path

root = Path(__file__).parent / "fabricdemogallery-fabriciq" / "healthcare"
py_compile.compile(str(root / "GettingStarted.Notebook" / "notebook-content.py"), doraise=True)
print("GettingStarted compiles OK")
for p in sorted(root.iterdir()):
    print(" ", p.name)
gs = (root / "GettingStarted.Notebook" / "notebook-content.py").read_text(encoding="utf-8")
print("docs-only        :", "notebookutils.notebook.run" not in gs and "_refresh_ontology" not in gs)
print("links cell kept  :", "_routes" in gs)
print("header intact    :", gs.startswith("# Fabric notebook source") and "default_lakehouse" in gs[:900])
