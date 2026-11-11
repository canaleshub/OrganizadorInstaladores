# -*- coding: utf-8 -*-
import shutil
from pathlib import Path
from datetime import datetime
from .common import load_config, load_json, save_json, data_path, report_path, human_size


def _safe_category_label(category):
    return str(category or "Otros").strip().replace("/", "_").replace("\\", "_").replace("..", "_") or "Otros"


def _unique_destination(relative_destination, used_destinations):
    """Evita colisiones de rutas, comparando sin distinguir mayusculas."""
    relative_destination = Path(relative_destination)
    candidate = relative_destination
    key = str(candidate).casefold()
    if key not in used_destinations:
        used_destinations.add(key)
        return candidate

    parent = relative_destination.parent
    suffix = relative_destination.suffix
    stem = relative_destination.stem
    counter = 2
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        key = str(candidate).casefold()
        if key not in used_destinations:
            used_destinations.add(key)
            return candidate
        counter += 1


def build_plan(scan_data, duplicate_data):
    cfg = load_config()
    roots = [Path(x).expanduser().resolve() for x in cfg.get("source_folders", [])]
    destination_text = cfg.get("destination_folder", "").strip()
    if not destination_text:
        raise ValueError("Destination folder is not configured (menu option 4).")
    destination = Path(destination_text).expanduser().resolve()

    planned = []
    seen_hashes = {}
    used_destinations = set()
    duplicate_dir_paths = {
        str(Path(x["duplicate"]).resolve())
        for x in duplicate_data.get("duplicate_directories", [])
    }

    for item in scan_data.get("files", []):
        source = Path(item["path"]).resolve()
        source_index = item.get("source_index")
        if source_index is None or source_index >= len(roots):
            continue
        root = roots[source_index]
        try:
            relative = source.relative_to(root)
        except ValueError:
            continue

        if any(str(parent.resolve()) in duplicate_dir_paths for parent in source.parents):
            planned.append({
                "source": str(source), "relative_destination": None,
                "action": "SKIP_DUPLICATE_DIRECTORY",
                "reason": "Exact duplicate directory"
            })
            continue

        digest = item.get("sha256")
        if digest and digest in seen_hashes:
            planned.append({
                "source": str(source), "relative_destination": None,
                "action": "SKIP_DUPLICATE_FILE",
                "reason": f"Duplicate of {seen_hashes[digest]}"
            })
            continue

        category = str(item.get("category") or "Otros").strip() or "Otros"
        category_label = _safe_category_label(category)

        # No incluir el nombre del directorio raiz configurado (filesA/filesB).
        # El arbol interno se conserva; si dos origenes producen la misma ruta,
        # se agrega un sufijo al archivo en conflicto para no sobrescribirlo.
        rel_dest = _unique_destination(
            Path(category_label) / relative,
            used_destinations
        )

        if digest:
            seen_hashes[digest] = str(source)

        planned.append({
            "source": str(source),
            "relative_destination": str(rel_dest),
            "destination": str(destination / rel_dest),
            "sha256": digest,
            "size": item.get("size", 0),
            "action": "COPY",
            "category": category,
            "source_root": str(root),
            "original_relative_path": str(relative)
        })

    return destination, planned


def preview_copy():
    scan_data = load_json(data_path("classified_results.json")) or load_json(data_path("scan_results.json"))
    duplicate_data = load_json(data_path("duplicates.json"))
    if not scan_data:
        raise FileNotFoundError("Run scan first.")
    if not duplicate_data:
        raise FileNotFoundError("Run duplicate analysis first (menu option 7).")
    destination, plan = build_plan(scan_data, duplicate_data)
    copies = [x for x in plan if x["action"] == "COPY"]
    skipped = len(plan) - len(copies)
    total_size = sum(x.get("size", 0) for x in copies)
    save_json(data_path("copy_plan.json"), {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "destination": str(destination),
        "copy_count": len(copies),
        "skipped_count": skipped,
        "total_size": total_size,
        "items": plan
    })
    print("\\nCOPY PREVIEW")
    print(f"Destination: {destination}")
    print(f"Files to copy: {len(copies)}")
    print(f"Duplicates skipped: {skipped}")
    print("\\nFiles by destination category:")
    category_counts = {}
    for item in copies:
        label = item.get("category", "Otros")
        category_counts[label] = category_counts.get(label, 0) + 1
    for label, count in sorted(category_counts.items()):
        print(f"  {label}: {count}")
    print(f"Estimated size: {human_size(total_size)}")
    print(f"Plan saved: {data_path('copy_plan.json')}")
    return plan


def execute_copy():
    cfg = load_config()
    plan_data = load_json(data_path("copy_plan.json"))
    if not plan_data:
        raise FileNotFoundError("Generate a copy preview first (menu option 8).")
    destination = Path(plan_data["destination"])
    destination.mkdir(parents=True, exist_ok=True)
    log = []
    copied = 0
    errors = 0
    for index, item in enumerate(plan_data["items"], 1):
        if item["action"] != "COPY":
            log.append({**item, "result": "SKIPPED"})
            continue
        src = Path(item["source"])
        dst = Path(item["destination"])
        try:
            if not src.exists():
                raise FileNotFoundError("Source file no longer exists.")
            if dst.exists() and not cfg.get("overwrite", False):
                log.append({**item, "result": "DESTINATION_EXISTS"})
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            from .scanner import sha256_file
            copied_hash = sha256_file(dst)
            if item.get("sha256") and copied_hash != item["sha256"]:
                raise IOError("SHA256 verification failed after copy.")
            copied += 1
            log.append({**item, "result": "COPIED", "verified_sha256": copied_hash})
        except Exception as exc:
            errors += 1
            log.append({**item, "result": "ERROR", "error": str(exc)})
        if index % 100 == 0:
            print(f"Processed copy items: {index}/{len(plan_data['items'])}")

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "destination": str(destination),
        "copied": copied,
        "errors": errors,
        "items": log
    }
    save_json(report_path("copy_report.json"), result)
    print("\\nCOPY COMPLETED")
    print(f"Copied: {copied}")
    print(f"Errors: {errors}")
    print(f"Report: {report_path('copy_report.json')}")
    return result
