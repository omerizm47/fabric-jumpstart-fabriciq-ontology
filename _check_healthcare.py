import py_compile
from pathlib import Path

root = Path(__file__).parent / "fabricdemogallery-fabriciq" / "healthcare"
py_compile.compile(str(root / "GettingStarted.Notebook" / "notebook-content.py"), doraise=True)
print("GettingStarted compiles OK")
for p in sorted(root.iterdir()):
    print(" ", p.name)
gs = (root / "GettingStarted.Notebook" / "notebook-content.py").read_text(encoding="utf-8")
print("has refresh fn :", "_refresh_ontology" in gs)
print("no 02 call     :", "02_create_ontology" not in gs)
param = (root / "parameter.yml").read_text(encoding="utf-8")
print("param rules    :", param.count("find_value:"), "entries")
