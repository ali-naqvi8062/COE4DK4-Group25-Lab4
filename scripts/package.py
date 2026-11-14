"""Package the simulator, scripts, measurements, and figures for submission."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from common import ROOT

destination = ROOT / "output/COE4DK4_Group25_Lab4_Code.zip"
files = [ROOT / name for name in ["README.md", "requirements.txt", ".gitignore", ".gitattributes"]]
for directory in ["src", "scripts", "docs", "results", "figures", "tables", "legacy"]:
    files.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                 and "__pycache__" not in p.parts and p.suffix != ".pyc")
with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
    for file in sorted(files):
        archive.write(file, file.relative_to(ROOT).as_posix())
with ZipFile(destination) as archive:
    assert archive.testzip() is None
    assert "src/arq.c" in archive.namelist()
    assert all(not x.endswith(".exe") for x in archive.namelist())
print(f"Packaged {len(files)} files: {destination.name}")
