# -*- coding: utf-8 -*-
import csv
from .common import load_json, data_path, report_path


def show_report():
    scan = load_json(data_path("classified_results.json")) or load_json(data_path("scan_results.json"))
    duplicates = load_json(data_path("duplicates.json"), {})
    if not scan:
        print("No hay resultados. Ejecuta primero el escaneo (opcion 5).")
        return
    print("\\nREPORTE DE INVENTARIO")
    print(f"Archivos: {scan.get('total_files', 0)}")
    print(f"Carpetas: {scan.get('total_directories', 0)}")
    print(f"Bytes totales: {scan.get('total_size', 0)}")
    print(f"Archivos duplicados: {duplicates.get('duplicate_file_count', 0)}")
    print(f"Carpetas duplicadas: {duplicates.get('duplicate_directory_count', 0)}")
    print("\\nCategorias (archivos + carpetas):")
    for name, count in sorted(scan.get("classification_summary", {}).items()):
        print(f"  {name}: {count}")
    export_csv(scan)


def export_csv(scan=None):
    if scan is None:
        scan = load_json(data_path("classified_results.json")) or load_json(data_path("scan_results.json"))
    if not scan:
        return
    path = report_path("inventory.csv")
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["item_type", "source_root", "relative_path", "name", "extension",
              "size", "modified", "sha256", "basic_type", "category", "classification_basis"]
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in scan.get("directories", []):
            output = dict(row)
            output.update(item_type="carpeta", extension="", size="", modified="", sha256="", basic_type="")
            writer.writerow(output)
        for row in scan.get("files", []):
            output = dict(row)
            output["item_type"] = "archivo"
            writer.writerow(output)
    print(f"CSV exportado: {path}")
