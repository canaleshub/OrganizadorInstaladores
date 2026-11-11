# -*- coding: utf-8 -*-
"""Genera un diccionario HTML del contenido realmente copiado al repositorio."""
import json
import webbrowser
from datetime import datetime
from pathlib import Path

from .common import load_config, load_json, report_path, ROOT

TEMPLATE_PATH = ROOT / "templates" / "dictionary_template.html"


def _json_for_html(data):
    # Evita que nombres de archivos puedan cerrar accidentalmente el script HTML.
    return (json.dumps(data, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026"))


def generate_dictionary(open_browser=True):
    cfg = load_config()
    destination_text = str(cfg.get("destination_folder", "")).strip()
    if not destination_text:
        raise ValueError("Primero configura la carpeta destino (opcion 4).")

    destination = Path(destination_text).expanduser().resolve()
    if not destination.is_dir():
        raise FileNotFoundError(
            "La carpeta destino no existe. Ejecuta primero la copia (opcion 9)."
        )

    copy_report = load_json(report_path("copy_report.json"), {})
    if not copy_report:
        raise FileNotFoundError(
            "No existe copy_report.json. Ejecuta primero la copia (opcion 9)."
        )

    copied_files = []
    for record in copy_report.get("items", []):
        if record.get("result") not in {"COPIED", "DESTINATION_EXISTS"}:
            continue
        target_text = record.get("destination")
        if not target_text:
            continue
        target = Path(target_text)
        if not target.is_file():
            continue
        try:
            relative = target.relative_to(destination)
        except ValueError:
            continue
        category = str(record.get("category") or relative.parts[0])
        copied_files.append({
            "name": target.name,
            "category": category,
            "relative": relative.as_posix(),
            "kind": "Archivo",
            "size": target.stat().st_size,
            "path": str(target),
        })

    if not copied_files:
        raise ValueError(
            "No se encontraron archivos copiados en el destino. Ejecuta la opcion 9 primero."
        )

    # Reconstruye las carpetas del repositorio a partir de los archivos presentes.
    directories = {}
    for item in copied_files:
        rel = Path(item["relative"])
        category = item["category"]
        for parent in reversed(rel.parents):
            if str(parent) == ".":
                continue
            relative = parent.as_posix()
            folder_path = destination / parent
            directories[str(folder_path).casefold()] = {
                "name": parent.name,
                "category": category,
                "relative": relative,
                "kind": "Carpeta",
                "size": None,
                "path": str(folder_path),
            }

    items = list(directories.values()) + copied_files
    items.sort(key=lambda x: (x["kind"], x["relative"].casefold()))
    payload = {"base": str(destination), "items": items}

    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"No se encontro la plantilla HTML: {TEMPLATE_PATH}")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html = template.replace("__DATA_JSON__", _json_for_html(payload))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = destination / f"Diccionario_{timestamp}.html"
    suffix = 2
    while output.exists():
        output = destination / f"Diccionario_{timestamp}_{suffix:02d}.html"
        suffix += 1
    output.write_text(html, encoding="utf-8")

    print("\nDICCIONARIO GENERADO")
    print(f"Ubicacion: {output}")
    print(f"Archivos: {len(copied_files)}")
    print(f"Carpetas: {len(directories)}")
    if open_browser:
        try:
            webbrowser.open(output.resolve().as_uri())
            print("Abriendo diccionario en el navegador...")
        except Exception as exc:
            print(f"No se pudo abrir automaticamente: {exc}")
    return output
