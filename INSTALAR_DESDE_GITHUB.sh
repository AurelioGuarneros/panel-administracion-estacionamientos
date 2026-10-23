#!/usr/bin/env bash
set -Eeuo pipefail

REPO="https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git"
BRANCH="respaldo-panel-20261023"
DEST="${HOME}/Documentos/panel-administracion-estacionamientos"
echo "=== Instalación de prueba: panel de estacionamientos ==="
echo "Sistema: $(uname -m) / $(uname -s)"
if [[ "$(uname -s)" != Linux ]]; then echo "Solo Linux (Ubuntu / Raspberry Pi OS)."; exit 1; fi
if ! command -v apt-get >/dev/null; then echo "Se requiere Ubuntu o Raspberry Pi OS con apt."; exit 1; fi
echo "Se instalarán dependencias del sistema (requiere sudo). No se alterarán bases de datos."
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip python3-tk python3-dev build-essential libmariadb-dev mariadb-client
mkdir -p "$(dirname "$DEST")"
if [[ -e "$DEST" ]]; then
  if [[ ! -d "$DEST/.git" ]]; then echo "ERROR: $DEST existe y no es repositorio Git. No se sobrescribe."; exit 1; fi
  cd "$DEST"
  if [[ -n "$(git status --porcelain)" ]]; then echo "ERROR: existen cambios locales. No se actualiza automáticamente."; exit 1; fi
  git fetch origin "$BRANCH"
  git switch "$BRANCH" 2>/dev/null || git switch -c "$BRANCH" --track "origin/$BRANCH"
  git pull --ff-only origin "$BRANCH"
else
  git clone --branch "$BRANCH" --single-branch "$REPO" "$DEST"
  cd "$DEST"
fi
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m compileall -q main.py Models Config Controller Views Tools actualizador_respaldos.py activador_respaldos.py panel_mejoras.py
chmod +x iniciar_linux.sh
echo
echo "Código y dependencias preparados en $DEST"
echo "IMPORTANTE: las configuraciones privadas y las bases de datos NO están en GitHub."
echo "No ejecute la aplicación hasta configurar los archivos locales de Config/config_files."
echo "Compruebe con: bash VERIFICAR_INSTALACION.sh"
