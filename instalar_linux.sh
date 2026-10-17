#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -f main.py ]]; then
  echo "Falta main.py: primero incorpora el código del panel." >&2
  exit 1
fi
command -v python3 >/dev/null || { echo "Instala Python 3"; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
echo "Dependencias Python instaladas."
echo "Asegura tener python3-tk y un cliente MariaDB/MySQL mediante tu gestor de paquetes."
echo "Configura las credenciales fuera de GitHub; luego ejecuta ./iniciar_linux.sh"
