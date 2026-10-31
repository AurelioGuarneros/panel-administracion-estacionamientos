# Resultados de validación de instaladores Windows

## Linux

Comando: `.venv/bin/python -B -m unittest discover -s tests -v`.

Resultado inicial de implementación: **155 pruebas correctas**. Incluye seis pruebas nuevas de instalación y reinstalación, cancelación, importación con respaldo sin modificar el origen, rechazo de importación incompleta, rutas del paquete y edición del catálogo desde la carpeta del usuario.

No hay Windows, Wine ni servidor gráfico Xvfb disponibles en este entorno Linux. No se afirma validación manual en Windows limpio.

## Windows / GitHub Actions

Pendiente de la primera compilación real. El flujo publica instaladores únicamente si pasan la compilación y las pruebas del instalador. Una ejecución fallida publica diagnóstico cuando hay archivos disponibles.

## Pendientes de aceptación

- Windows 10 y Windows 11 limpios sin Python ni Git: instalación por doble clic y primer inicio sin conexión.
- Interacción manual con contraseña, cancelación e importación de una copia de instalación anterior.
- Recorrido visual de todas las interfaces, reportes y selección de temas.
- Prueba del instalador independiente de herramientas en Windows limpio.
- Prueba de actualización desde una compilación anterior del paquete cuando exista.
- Reportes contra servidor configurado y PDF con Excel instalado, fuera del alcance de esta etapa sin MariaDB.
