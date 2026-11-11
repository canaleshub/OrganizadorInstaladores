# -*- coding: utf-8 -*-
import os
import hashlib
from pathlib import Path
from datetime import datetime
from .common import load_config, save_json, data_path, human_size

ARCHIVE_EXTENSIONS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"}
INSTALLER_EXTENSIONS = {".exe", ".msi", ".msix", ".appx", ".appxbundle", ".msp", ".cab", ".iso", ".pkg", ".deb", ".rpm", ".apk"}
TRADING_EXTENSIONS = {".ex4", ".ex5", ".mq4", ".mq5", ".set", ".tpl", ".mqh"}
DOCUMENT_EXTENSIONS = {".pdf", ".txt", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".html", ".htm"}
MEDIA_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mp3", ".wav", ".jpg", ".jpeg", ".png"}

def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()

def basic_type(path):
    ext = Path(path).suffix.lower()
    if ext in INSTALLER_EXTENSIONS:
        return "Installer / package"
    if ext in ARCHIVE_EXTENSIONS:
        return "Compressed archive"
    if ext in TRADING_EXTENSIONS:
        return "Trading resource"
    if ext in DOCUMENT_EXTENSIONS:
        return "Document"
    if ext in MEDIA_EXTENSIONS:
        return "Media"
    if ext in {".dll", ".sys", ".ocx"}:
        return "Library / system component"
    return "Other file"

def inspect_archive(path):
    """List ZIP/TAR contents without extracting. Other archive formats are recorded, not opened."""
    result = {"inspected": False, "entries": [], "entry_count": None, "note": ""}
    suffix = Path(path).suffix.lower()
    try:
        if suffix == ".zip":
            import zipfile
            with zipfile.ZipFile(path, "r") as z:
                infos = z.infolist()
                result.update(inspected=True, entry_count=len(infos),
                              entries=[{"name": i.filename, "size": i.file_size, "is_dir": i.is_dir()} for i in infos[:5000]])
        elif suffix in {".tar", ".gz", ".bz2", ".xz", ".tgz"}:
            import tarfile
            with tarfile.open(path, "r:*") as t:
                members = t.getmembers()
                result.update(inspected=True, entry_count=len(members),
                              entries=[{"name": m.name, "size": m.size, "is_dir": m.isdir()} for m in members[:5000]])
        else:
            result["note"] = "Format not inspected internally; archive itself is inventoried and hashed."
    except Exception as exc:
        result["note"] = f"Archive inspection failed: {exc}"
    return result

def scan():
    cfg = load_config()
    roots = cfg.get("source_folders", [])
    if not roots:
        raise ValueError("No source folders configured. Use menu option 1.")
    records, errors, directories = [], [], []
    seen_paths = set()
    total = 0
    for root_index, root_text in enumerate(roots):
        root = Path(root_text).expanduser()
        if not root.exists() or not root.is_dir():
            errors.append({"path": str(root), "error": "Source folder does not exist or is not a directory."})
            continue
        root = root.resolve()
        print(f"Scanning: {root}")
        for current, dirnames, filenames in os.walk(root, followlinks=False):
            current_path = Path(current)
            if cfg.get("skip_symlinks", True):
                dirnames[:] = [d for d in dirnames if not (current_path / d).is_symlink()]
            directories.append({
                "source_index": root_index,
                "source_root": str(root),
                "path": str(current_path),
                "relative_path": str(current_path.relative_to(root)),
                "name": current_path.name,
                "is_empty_at_scan": not dirnames and not filenames
            })
            for filename in filenames:
                path = current_path / filename
                try:
                    if cfg.get("skip_symlinks", True) and path.is_symlink():
                        continue
                    stat = path.stat()
                    resolved = str(path.resolve())
                    if resolved in seen_paths:
                        continue
                    seen_paths.add(resolved)
                    total += 1
                    record = {
                        "id": total,
                        "source_index": root_index,
                        "source_root": str(root),
                        "path": str(path),
                        "relative_path": str(path.relative_to(root)),
                        "name": filename,
                        "extension": path.suffix.lower(),
                        "size": stat.st_size,
                        "size_human": human_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
                        "basic_type": basic_type(path),
                        "sha256": None,
                        "hash_error": None,
                        "archive": None
                    }
                    try:
                        record["sha256"] = sha256_file(path)
                    except Exception as exc:
                        record["hash_error"] = str(exc)
                    # Archive files are inventoried and hashed as opaque files; never inspect their contents.
                    record["archive"] = None
                    records.append(record)
                    if total % 100 == 0:
                        print(f"Files scanned: {total}")
                except Exception as exc:
                    errors.append({"path": str(path), "error": str(exc)})
    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_folders": roots,
        "total_files": len(records),
        "total_directories": len(directories),
        "total_size": sum(x["size"] for x in records),
        "directories": directories,
        "files": records,
        "errors": errors
    }
    save_json(data_path("scan_results.json"), result)
    print(f"\nScan completed. Files: {len(records)} | Directories: {len(directories)} | Errors: {len(errors)}")
    print(f"Saved: {data_path('scan_results.json')}")
    return result
