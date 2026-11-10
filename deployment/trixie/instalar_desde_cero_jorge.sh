#!/usr/bin/env bash
# Instalacion inicial de prueba en Raspberry Pi OS Trixie.
set -Eeuo pipefail
trap 'echo "ERROR en linea $LINENO. Instalacion detenida." >&2' ERR
REPO='https://github.com/AurelioGuarneros/panel-administracion-estacionamientos.git'
RAMA='desarrollo/sincronizar-autorizaciones-jorge'
DESTINO="$HOME/panel-administracion-estacionamientos-jorge"
PERFIL="$HOME/.config/panel-estacionamientos/recuperacion.json"
[[ $EUID -ne 0 ]] || { echo 'Ejecutar como pi, sin sudo.' >&2; exit 1; }
. /etc/os-release
[[ "${VERSION_CODENAME:-}" == trixie ]] || { echo 'Se requiere Trixie.' >&2; exit 1; }
[[ ! -e "$DESTINO" && ! -e "$PERFIL" ]] || { echo 'Ya hay una instalacion o perfil; no se sobrescriben.' >&2; exit 1; }
echo "Se instalara el panel en $DESTINO, MariaDB y el auxiliar de recuperacion."
echo 'No se descargaran bases automaticamente.'
read -r -p 'Escribe INSTALAR para continuar: ' confirmacion
[[ "$confirmacion" == INSTALAR ]] || exit 0
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-venv python3-tk python3-pip python3-pymysql mariadb-server mariadb-client sudo ca-certificates libmariadb-dev build-essential
sudo systemctl enable --now mariadb
git clone --branch "$RAMA" --single-branch "$REPO" "$DESTINO"
cd "$DESTINO"
test -f main.py
test -f deployment/trixie/preparar_sistema.py
bash instalar_linux.sh
.venv/bin/python -B -m unittest discover -s tests
echo 'Ahora se solicitaran datos IMAP del correo receptor.'
.venv/bin/python Tools/configurar_respaldos.py
test -f "$PERFIL"
sudo /usr/bin/python3 deployment/trixie/preparar_sistema.py --usuario "$USER" --perfil "$PERFIL"
sudo /usr/bin/python3 deployment/trixie/preparar_sistema.py --usuario "$USER" --perfil "$PERFIL" --instalar
sudo visudo -cf /etc/sudoers.d/panel-estacionamientos
echo 'INSTALACION BASE COMPLETADA.'
echo "Para iniciar: cd '$DESTINO' && bash iniciar_linux.sh"
echo 'PENDIENTE: verificar GUI, correo e importacion de bases reales.'
