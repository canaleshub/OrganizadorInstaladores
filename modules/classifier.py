# -*- coding: utf-8 -*-
"""Clasificacion por nombre propio en el primer nivel y herencia estricta."""
import re
import unicodedata
from pathlib import Path

from .common import load_json, save_json, data_path, ROOT

CATEGORIES_PATH = ROOT / "categorias.json"


def normalize(value):
    value = str(value or "")
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    value = re.sub(r"(?<=[A-Za-z])(?=[0-9])|(?<=[0-9])(?=[A-Za-z])", " ", value)
    value = value.casefold()
    value = value.replace("c#", " c sharp ").replace("c++", " c plus plus ")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("-", " ").replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def contains_keyword(name, keyword):
    normalized_name = normalize(name)
    normalized_keyword = normalize(keyword)
    if not normalized_keyword or len(normalized_keyword) < 2:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(normalized_keyword) + r"(?![a-z0-9])"
    if re.search(pattern, normalized_name):
        return True

    # Segunda comparación para nombres de producto escritos en CamelCase,
    # por ejemplo HeidiSQL: no se debe perder la coincidencia al separar
    # artificialmente las mayúsculas internas del nombre.
    compact_name = re.sub(r"[^a-z0-9]+", " ", str(name or "").casefold()).strip()
    compact_keyword = normalized_keyword.replace(" ", "")
    return bool(compact_keyword and re.search(
        r"(?<![a-z0-9])" + re.escape(compact_keyword) + r"(?![a-z0-9])",
        compact_name
    ))


def load_categories():
    if not CATEGORIES_PATH.is_file():
        raise FileNotFoundError("No se encontro categorias.json junto a main.py.")
    catalogue = load_json(CATEGORIES_PATH, {})
    if not isinstance(catalogue.get("categorias"), list) or not catalogue["categorias"]:
        raise ValueError("categorias.json no contiene una lista 'categorias' valida.")
    return catalogue


def classify_name(main_name, catalogue):
    """Clasifica exclusivamente el nombre recibido; gana la primera coincidencia."""
    for category in catalogue["categorias"]:
        label = category.get("nombre", "Otros")
        for keyword in category.get("palabras_clave", []):
            if contains_keyword(main_name, keyword):
                return label
    return catalogue.get("categoria_predeterminada", "Otros")


def _relative_path(record):
    value = record.get("relative_path")
    if value:
        return Path(value)
    path = Path(record.get("path", ""))
    root = Path(record.get("source_root", ""))
    try:
        return path.relative_to(root)
    except (ValueError, OSError):
        return Path(path.name)


def _depth(relative):
    if str(relative) in ("", "."):
        return 0
    return len(relative.parts)


def _path_key(value):
    # casefold hace que la busqueda de padres sea compatible con Windows.
    return str(Path(value).resolve()).casefold()


def classify_all():
    data = load_json(data_path("scan_results.json"))
    if not data:
        raise FileNotFoundError("Primero ejecuta el escaneo (opcion 5).")
    catalogue = load_categories()
    default_category = catalogue.get("categoria_predeterminada", "Otros")

    # Las carpetas raiz configuradas son contenedores, no se clasifican.
    # Solo las carpetas inmediatamente dentro de cada origen se clasifican
    # por su propio nombre. Todas las subcarpetas heredan esa categoria.
    directories = [dict(item) for item in data.get("directories", [])]
    directories.sort(key=lambda item: _depth(_relative_path(item)))

    directory_categories = {}
    classified_directories = []

    for item in directories:
        rel = _relative_path(item)
        depth = _depth(rel)
        path = item.get("path", "")
        name = item.get("name") or Path(path).name

        if depth == 0:
            category = default_category
            basis = "raiz_origen_contenedor"
        elif depth == 1:
            category = classify_name(name, catalogue)
            basis = "nombre_propio_carpeta_principal"
        else:
            parent_path = str(Path(path).parent)
            category = directory_categories.get(_path_key(parent_path), default_category)
            basis = "heredada_de_carpeta_principal"

        directory_categories[_path_key(path)] = category
        classified_directories.append({
            **item,
            "name": name,
            "category": category,
            "classification_basis": basis
        })

    # Los archivos directamente en la raiz del origen son independientes y
    # se clasifican por su nombre. Los archivos dentro de cualquier carpeta
    # heredan la categoria de la carpeta principal; no se inspeccionan sus
    # nombres, extensiones ni contenidos para cambiar dicha categoria.
    files = []
    for original in data.get("files", []):
        item = dict(original)
        rel = _relative_path(item)
        parent_rel = rel.parent
        name = item.get("name") or Path(item.get("path", "")).name

        if _depth(parent_rel) == 0:
            category = classify_name(name, catalogue)
            basis = "nombre_propio_archivo_independiente"
        else:
            parent_path = str(Path(item.get("path", "")).parent)
            category = directory_categories.get(_path_key(parent_path), default_category)
            basis = "heredada_de_carpeta_principal"

        files.append({
            **item,
            "name": name,
            "category": category,
            "classification_basis": basis
        })

    file_summary, directory_summary = {}, {}
    for item in files:
        label = item["category"]
        file_summary[label] = file_summary.get(label, 0) + 1
    for item in classified_directories:
        label = item["category"]
        directory_summary[label] = directory_summary.get(label, 0) + 1

    summary = dict(file_summary)
    for label, count in directory_summary.items():
        summary[label] = summary.get(label, 0) + count

    result = {
        **data,
        "classification_catalogue_version": catalogue.get("version", "unknown"),
        "classification_rule": (
            "Carpetas de primer nivel: solo nombre propio. Subcarpetas y "
            "archivos internos: heredan la categoria de la carpeta principal. "
            "Archivos directamente en la raiz: solo nombre propio. "
            "Nunca se analizan descendientes para inferir categorias."
        ),
        "classification_summary": summary,
        "file_classification_summary": file_summary,
        "directory_classification_summary": directory_summary,
        "files": files,
        "directories": classified_directories
    }
    save_json(data_path("classified_results.json"), result)

    print("\\nRESUMEN DE CLASIFICACION")
    print("Archivos:")
    for label, count in sorted(file_summary.items()):
        print(f"  {label}: {count}")
    print("Carpetas:")
    for label, count in sorted(directory_summary.items()):
        print(f"  {label}: {count}")
    print(f"\\nTotal de elementos clasificados: {len(files) + len(classified_directories)}")
    print(f"Guardado: {data_path('classified_results.json')}")
    return result
