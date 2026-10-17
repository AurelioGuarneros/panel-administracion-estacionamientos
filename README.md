# Panel de Administración de Estacionamientos

Aplicación Python/Tkinter para consultar ingresos, boletos, pensionados y reportes, de manera independiente del sistema Entrada/TPV/Salida.

## Estado
**Repositorio preparado; código original pendiente de incorporación.** No hay instalador compilado ni ejecución verificada todavía.

## Flujo que se debe conservar
1. Seleccionar estacionamiento.
2. Identificar su cuenta de correo asociada.
3. Pulsar el botón **Cargar información**.
4. Descargar el respaldo ZIP recibido por correo (IMAP).
5. Importar a la base local de consulta.
6. Mostrar claramente la **fecha del último corte disponible**, diferenciada de la fecha del correo.

## Compatibilidad prevista
Windows, Linux de escritorio y Raspberry Pi OS. La adaptación de dependencias y rutas específicas de Windows aún requiere pruebas.

## Seguridad
No publicar contraseñas, tokens, archivos de configuración con credenciales, correos privados ni copias reales de bases de datos. Cada instalación debe configurar localmente sus secretos; consultar `.gitignore`.

## Próximos pasos
Incorporar el código fuente depurado, preservar la versión original, probar dependencias y generar instaladores para cada sistema operativo.

Repositorio relacionado: [Sistema de Estacionamiento Raspberry](https://github.com/AurelioGuarneros/sistema-estacionamiento-raspberry).
