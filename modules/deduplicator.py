# -*- coding: utf-8 -*-
from collections import defaultdict
from pathlib import Path
from .common import load_json, save_json, data_path

def directory_fingerprints(scan_data):
    """Fingerprint a directory by relative file names and file hashes, including nested paths."""
    files_by_root = defaultdict(list)
    for item in scan_data.get("files", []):
        key = (item["source_index"], item["source_root"])
        files_by_root[key].append(item)

    dirs = scan_data.get("directories", [])
    result = []
    for directory in dirs:
        root = directory["source_root"]
        source_index = directory["source_index"]
        base = Path(directory["path"])
        entries = []
        for item in files_by_root[(source_index, root)]:
            try:
                rel = Path(item["path"]).relative_to(base)
            except ValueError:
                continue
            if item.get("sha256"):
                entries.append((str(rel).replace("\\", "/").lower(), item["sha256"]))
        entries.sort()
        if not entries:
            # Empty folders are not deduplicated automatically.
            continue
        result.append({
            "source_index": source_index,
            "path": directory["path"],
            "relative_path": directory["relative_path"],
            "fingerprint": tuple(entries),
            "file_count": len(entries)
        })
    return result

def detect_duplicates():
    data = load_json(data_path("classified_results.json")) or load_json(data_path("scan_results.json"))
    if not data:
        raise FileNotFoundError("Run scan first.")
    groups = defaultdict(list)
    for item in data.get("files", []):
        digest = item.get("sha256")
        if digest:
            groups[digest].append(item)

    duplicates = []
    duplicate_paths = set()
    unique_files = []
    for digest, items in groups.items():
        items.sort(key=lambda x: (x.get("source_index", 999999), len(x.get("path", "")), x.get("path", "").lower()))
        keeper = items[0]
        unique_files.append({"sha256": digest, "kept": keeper["path"], "size": keeper["size"]})
        for duplicate in items[1:]:
            duplicate_paths.add(duplicate["path"])
            duplicates.append({
                "type": "file",
                "sha256": digest,
                "kept": keeper["path"],
                "duplicate": duplicate["path"],
                "size": duplicate["size"]
            })

    # Exact directory duplicates: same relative tree paths and same file hashes.
    dir_groups = defaultdict(list)
    for item in directory_fingerprints(data):
        dir_groups[item["fingerprint"]].append(item)

    duplicate_directories = []
    for fingerprint, items in dir_groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: (x["source_index"], len(x["path"]), x["path"].lower()))
        keeper = items[0]
        for duplicate in items[1:]:
            duplicate_directories.append({
                "type": "directory",
                "kept": keeper["path"],
                "duplicate": duplicate["path"],
                "file_count": duplicate["file_count"]
            })

    result = {
        "total_files": len(data.get("files", [])),
        "unique_file_hashes": len(groups),
        "duplicate_file_count": len(duplicates),
        "duplicate_files": duplicates,
        "duplicate_directory_count": len(duplicate_directories),
        "duplicate_directories": duplicate_directories,
        "note": "Duplicates are not deleted from source. They are excluded from the destination copy. Directory duplicates are reported; file-level SHA256 deduplication is authoritative during copy."
    }
    save_json(data_path("duplicates.json"), result)
    print("\nDUPLICATE ANALYSIS")
    print(f"Files scanned: {result['total_files']}")
    print(f"Unique SHA256 groups: {result['unique_file_hashes']}")
    print(f"Duplicate file copies: {result['duplicate_file_count']}")
    print(f"Exact duplicate directories: {result['duplicate_directory_count']}")
    print(f"Saved: {data_path('duplicates.json')}")
    return result
