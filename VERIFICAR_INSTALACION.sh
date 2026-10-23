#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
echo "=== Verificación sin conexión a correo ni importación SQL ==="
echo "Rama: $(git branch --show-current)"
echo "Commit: $(git rev-parse --short HEAD)"
if [[ ! -x .venv/bin/python ]]; then echo "FALTA entorno virtual"; exit 1; fi
.venv/bin/python - <<'PY'
import importlib
mods=['tkinter','pymysql','PIL','tkcalendar','ttkthemes','xlsxwriter','openpyxl','Crypto','dateutil','requests']
failed=[]
for mod in mods:
    try: importlib.import_module(mod); print("OK:",mod)
    except Exception as e: failed.append(mod); print("ERROR:",mod,type(e).__name__)
if failed: raise SystemExit(1)
PY
status=$?
if [[ $status -ne 0 ]]; then exit "$status"; fi
for name in path_files_settings.json database_connection_configuration.json system_settings.json; do
  if [[ -f "Config/config_files/$name" ]]; then echo "PRESENTE: $name"; else echo "PENDIENTE (privado): $name"; fi
done
echo "Verificación de dependencias terminada. No confirma funcionamiento con bases ni correo."
