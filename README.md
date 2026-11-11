# Organizador Inteligente de Archivos

Aplicacion de consola en Python para inventariar archivos y carpetas, clasificar por nombre principal, detectar duplicados exactos y copiar los archivos organizados físicamente por categoria.

## Requisitos

- Windows 10/11, Linux o macOS.
- Python 3.9 o superior.
- No requiere instalar paquetes externos.

## Instalacion

1. Extrae el ZIP en una carpeta, por ejemplo `C:\OrganizadorInteligente`.
2. Abre PowerShell o CMD en esa carpeta.
3. Ejecuta:

```powershell
python main.py
```

## Primer uso

1. Opcion 1: agrega cada carpeta de origen (por ejemplo `D:\INSTALADORES` y `D:\ARCHIVOS`).
2. Opcion 4: configura el disco/carpeta destino (por ejemplo `E:\REPOSITORIO`).
3. Opcion 5: escanea. Se recorren subcarpetas y se calculan hashes SHA256.
4. Opcion 6: clasifica archivos y carpetas usando exclusivamente su nombre principal. La clasificacion es informativa; no cambia rutas.
5. Opcion 7: detecta duplicados.
6. Opcion 8: revisa la vista previa.
7. Opcion 9: confirma el copiado.
8. Opcion 10: consulta el resumen y exporta CSV.
9. Opcion 11: genera el diccionario HTML dentro de la carpeta destino y lo abre en el navegador.

## Politica de conservacion

- Los originales nunca se eliminan ni modifican.
- El destino organiza físicamente los archivos por categoria.
- Dentro de cada categoria se conserva el nombre de la carpeta de origen y la ruta relativa interna. Esto evita colisiones entre origenes y mantiene la estructura de subcarpetas.
- Ejemplo: `E:\REPOSITORIO\Trading\filesB\RSI Arrows V4 EA\...`.
- La categoria se asigna por el nombre principal del archivo; no se usa extension, ruta, contenido ni contexto.
- Las carpetas de categoria se crean automaticamente durante la copia. No se crean carpetas para categorias sin archivos copiados.
- Los archivos identicos se comparan por SHA256. Se copia una sola instancia fisica al destino; las repeticiones se registran en `data/duplicates.json` y `reports/copy_report.json`.
- Los directorios idénticos se detectan y reportan. La deduplicacion efectiva por archivo se hace por SHA256 para no borrar contenido distinto ni asumir que carpetas con nombres iguales son iguales.
- Los comprimidos (ZIP/RAR/7Z y otros) se inventarian y calculan por SHA256 como un unico archivo. Nunca se abre su contenido interno.
- Se copian todos los tipos de archivo, no solo EXE. Esto incluye `.set`, `.ex4`, `.zip`, `.rar`, `.iso`, documentos, videos y archivos auxiliares.
- No se ejecutan instaladores ni se extraen archivos comprimidos.

## Importante sobre duplicados y estructura

Cuando un archivo duplicado aparece en dos rutas diferentes, el programa conserva una sola copia física en la primera ruta elegida y registra la otra ruta como duplicada. Por tanto, esa segunda ruta puede quedar sin ese archivo en el destino. Las carpetas padre se mantienen cuando contienen otros archivos o son necesarias para la estructura.

## Datos y reportes

- `data/scan_results.json`: inventario del escaneo.
- `data/classified_results.json`: inventario con clasificación.
- `data/duplicates.json`: duplicados detectados.
- `data/copy_plan.json`: vista previa del copiado.
- `reports/inventory.csv`: inventario para Excel.
- `reports/copy_report.json`: resultado del copiado.

## Recomendaciones

- Prueba primero con carpetas pequeñas y un destino vacío.
- Asegúrate de tener espacio suficiente.
- No configures como destino una carpeta dentro de los orígenes.
- Si cambian los archivos de origen, vuelve a escanear, clasificar, detectar duplicados y generar la vista previa antes de copiar.
- Si un archivo no puede leerse, se registra un error y no se considera seguro para deduplicar.


## Clasificacion por nombre principal

- El catalogo editable esta en `categorias.json`, junto a `main.py`.
- Se clasifican archivos y carpetas.
- La unica entrada es el nombre del propio elemento: nombre de archivo, carpeta, ZIP/RAR o instalador.
- No se usa extension, carpeta padre, ruta relativa, contenido ni contenido interno de comprimidos.
- Se normalizan mayusculas/minusculas, acentos, guiones y guiones bajos.
- Las categorias se evalúan en el orden de `categorias.json`; gana la primera coincidencia.
- Si no hay coincidencia, se asigna `Otros`.
- Edita `categorias.json` para ampliar palabras clave sin modificar el codigo.
- La categoria determina la carpeta de destino donde se copia cada archivo; no se mueve, renombra ni modifica el original.
- La estructura de origen se conserva debajo de la carpeta de categoria.
- `reports/inventory.csv` incluye archivos y carpetas con su categoria.


### HTML repository dictionary

After copying files to the destination (option 9), use option 11 to generate a searchable HTML index in the destination folder. The filename uses `Diccionario_YYYYMMDD_HHMM.html` (for example, `Diccionario_20260911_2208.html`). If a file with that name already exists, a numeric suffix is added to avoid overwriting it. The dictionary indexes files that are present in the destination and their parent folders; it does not move or modify repository files.
