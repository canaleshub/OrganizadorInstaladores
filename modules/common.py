# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
DATA_DIR = ROOT / "data"
REPORT_DIR = ROOT / "reports"

def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    temp.replace(path)

def load_config():
    cfg = load_json(CONFIG_PATH, {})
    cfg.setdefault("source_folders", [])
    cfg.setdefault("destination_folder", "")
    cfg.setdefault("copy_all_files", True)
    cfg.setdefault("hash_algorithm", "sha256")
    cfg.setdefault("skip_symlinks", True)
    cfg.setdefault("archive_inspection", False)
    cfg.setdefault("preserve_empty_directories", True)
    cfg.setdefault("overwrite", False)
    cfg.setdefault("report_folder", "reports")
    cfg.setdefault("data_folder", "data")
    return cfg

def data_path(name):
    return ROOT / load_config().get("data_folder", "data") / name

def report_path(name):
    return ROOT / load_config().get("report_folder", "reports") / name

def human_size(size):
    value = float(size or 0)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} TB"
