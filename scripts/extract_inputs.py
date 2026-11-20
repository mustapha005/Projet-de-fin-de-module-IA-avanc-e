"""Keep a local, searchable copy of the user-provided project specifications."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / "Downloads"
NAMES = ["SAN1_master_prompt.md", "Catalogue_Questions_Recherche_IA_Avancee.docx",
         "Directives_Projet_Fin_Module_IA_Avancee.docx"]


def main():
    output = ROOT / ".inputs"
    output.mkdir(exist_ok=True)
    manifest = []
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    for name in NAMES:
        source = SOURCE / name
        shutil.copy2(source, output / name)
        manifest.append({"filename": name, "sha256": sha256(source.read_bytes()).hexdigest()})
        if source.suffix == ".docx":
            with ZipFile(source) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
                paragraphs = ["".join(t.text or "" for t in par.findall(".//w:t", ns))
                              for par in root.findall(".//w:p", ns)]
            (output / (source.stem + ".txt")).write_text("\n".join(paragraphs), encoding="utf-8")
    (ROOT / "docs" / "input_sources.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Archived and extracted 3 source files locally; hashes recorded.")


if __name__ == "__main__":
    main()
