# Preparación de versión Raspberry Pi OS Trixie

Referencia local de main conservada: `3c4c943dbf80930e6759f59e412f82a015381870`.
Main remoto observado (solo lectura): `360d074344184ffaf4f3b1339f2a6d3266e49e04`.
No coincide con main local; ninguno se modifica en esta entrega.
HEAD local antes de preparar la entrega: `c6ee8d797afa7230823ed487ca2b7af35d708943`.

La rama se prepara desde `9f3558ba9fda3d42af4758a70a34158c276fc323`, anterior a la
incorporación del código, y recibe los archivos actuales. Así se excluye una credencial
que existe en Tools/a.txt en el historial posterior. No se reescribe main ni se publica
la rama local de recuperación. Tools/a.txt permanece en la instalación y no se publica.

La copia privada de recuperación está en
`recuperacion_publicacion/20261029_223905_367959/instalacion_completa.tar.gz`.
Incluye archivos de configuración reales y metadatos Git; excluye el entorno virtual,
que se puede reinstalar. `referencias.json` contiene referencias y SHA-256 de la copia.
Este directorio completo está excluido de Git.

## Recuperar sin sobrescribir la instalación actual

Para consultar el main anterior, usar otro directorio y, si el objeto está disponible:

```bash
git worktree add --detach ../panel-main-anterior 3c4c943dbf80930e6759f59e412f82a015381870
```

No se presupone que un clon de solo raspberry-trixie contenga ese objeto.
Alternativamente, extraer la copia privada en un directorio nuevo y vacío, conservando
su carácter privado, y reconstruir el entorno virtual. No extraer sobre la instalación
actual. Cambiar de versión del código no restaura bases MariaDB ni el estado externo.

## Validación previa a publicación

Prueba gráfica aislada aprobada, con servicios externos bloqueados y datos ficticios.
85 pruebas unitarias pasan, incluidas 8 de eliminación de catálogo: confirmación,
permisos, reserva de identidades, repetición, fallo de guardado y conservación del
histórico. No se cambiaron contraseñas, permisos de acceso ni bases de datos reales.
Los módulos de correo y respaldos conservan su comportamiento; no se instala su
complemento en la interfaz.

Commit propuesto: `Preparar panel de catálogo y estado local para pruebas en Raspberry Pi OS Trixie`.
Etiqueta propuesta: `v2026.10.29-trixie-pruebas.1`.
Commit, etiqueta y publicación pendientes de autorización final.
