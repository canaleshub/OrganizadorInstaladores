# -*- coding: utf-8 -*-
from pathlib import Path
from .common import load_config, save_json, CONFIG_PATH
from .scanner import scan
from .classifier import classify_all
from .deduplicator import detect_duplicates
from .copier import preview_copy, execute_copy
from .reports import show_report
from .dictionary import generate_dictionary

def pause():
    input("\nPress Enter to continue...")

def show_menu():
    print("\n" + "=" * 62)
    print("       ORGANIZADOR INTELIGENTE DE ARCHIVOS")
    print("=" * 62)
    print("[1] Add source folder")
    print("[2] Remove source folder")
    print("[3] Show source folders")
    print("[4] Configure destination folder")
    print("[5] Scan files and folders")
    print("[6] Classify inventory")
    print("[7] Detect duplicates (SHA256)")
    print("[8] Preview copy operation")
    print("[9] Execute copy")
    print("[10] View report / export CSV")
    print("[11] Generate HTML dictionary")
    print("[12] Exit")
    print("=" * 62)

def run():
    while True:
        show_menu()
        option = input("Select an option: ").strip()
        try:
            cfg = load_config()
            if option == "1":
                path = input("Source folder path: ").strip().strip('"')
                p = Path(path).expanduser()
                if not p.exists() or not p.is_dir():
                    print("[ERROR] Folder does not exist.")
                else:
                    resolved = str(p.resolve())
                    if resolved not in cfg["source_folders"]:
                        cfg["source_folders"].append(resolved)
                        save_json(CONFIG_PATH, cfg)
                        print("[OK] Source folder added.")
                    else:
                        print("[INFO] Folder already registered.")
            elif option == "2":
                for i, p in enumerate(cfg["source_folders"], 1):
                    print(f"[{i}] {p}")
                value = input("Number to remove: ").strip()
                if value.isdigit() and 1 <= int(value) <= len(cfg["source_folders"]):
                    removed = cfg["source_folders"].pop(int(value) - 1)
                    save_json(CONFIG_PATH, cfg)
                    print(f"[OK] Removed: {removed}")
                else:
                    print("[ERROR] Invalid selection.")
            elif option == "3":
                print("\nSOURCE FOLDERS")
                for i, p in enumerate(cfg["source_folders"], 1):
                    print(f"[{i}] {p}")
                if not cfg["source_folders"]:
                    print("No source folders configured.")
            elif option == "4":
                path = input("Destination folder path: ").strip().strip('"')
                if not path:
                    print("[ERROR] Empty destination.")
                else:
                    dest = Path(path).expanduser().resolve()
                    # Prevent copying a source into itself or into a child of a source.
                    invalid = False
                    for source in cfg["source_folders"]:
                        s = Path(source).expanduser().resolve()
                        try:
                            dest.relative_to(s)
                            invalid = True
                            break
                        except ValueError:
                            pass
                    if invalid:
                        print("[ERROR] Destination cannot be inside a source folder.")
                    else:
                        cfg["destination_folder"] = str(dest)
                        save_json(CONFIG_PATH, cfg)
                        print(f"[OK] Destination configured: {dest}")
            elif option == "5":
                scan()
            elif option == "6":
                classify_all()
            elif option == "7":
                detect_duplicates()
            elif option == "8":
                preview_copy()
            elif option == "9":
                confirm = input("This will COPY files to destination. Continue? (yes/no): ").strip().lower()
                if confirm == "yes":
                    execute_copy()
                else:
                    print("Copy cancelled.")
            elif option == "10":
                show_report()
            elif option == "11":
                generate_dictionary()
            elif option == "12":
                print("Goodbye.")
                break
            else:
                print("[ERROR] Invalid option.")
        except Exception as exc:
            print(f"[ERROR] {exc}")
        pause()
