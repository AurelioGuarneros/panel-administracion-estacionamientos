# Estado del proyecto de estacionamientos
Actualizado: 24 de octubre de 2026. Registro inicial basado en conversaciones; validar estados contra código y pruebas.

## Propósito
Evitar duplicar trabajo y preservar decisiones. Prioridad inmediata: integrar las mejoras visuales de Jorge a la TPV y generar un instalador Ubuntu, sin alterar funciones que ya operan.

## Antecedentes
- Aurelio creó la base Python y base de datos que funcionó durante años.
- Noé reestructuró el programa y añadió consultas por correo.
- Aurelio y ChatGPT trabajan en consultas, TPV e instalador.
- Jorge creó mejoras de pantallas que ya funcionan en algunos estacionamientos; ubicación y versión de sus archivos por confirmar (memoria, computadora o Raspberry).

## Inventario provisional
| Componente | Situación | Acción |
|---|---|---|
| Entrada, TPV, salida, barreras | Sistema base histórico funcional | Verificar regresión |
| Consultas por correo | Desarrolladas por Noé | Confirmar en versión actual |
| Consultas, incluido Aguascalientes | Ya revisadas en sesiones previas; alcance exacto por auditar | No repetir sin evidencia de fallo |
| Pantallas TPV de Jorge | Funcionan en algunas instalaciones, no integradas aún a nuestra línea | Recuperar, comparar, aprobar |
| Instalador Ubuntu | Pendiente | Empaquetar y probar |
| Cajero con billetes y cambio | Diseño futuro | No implementar aún |
| Cobro bancario sin contacto y aplicación | Investigación/diseño futuro | Evaluar proveedor certificado |
| Elevador de automóviles | Diseño futuro | Analizar seguridad por separado |

## Reglas para ChatGPT, Codex y colaboradores
1. Leer este archivo antes de iniciar una tarea y comprobar el código real.
2. Registrar qué existe, qué falta y qué ya se probó. Nunca asumir que una conversación prueba que algo funciona.
3. Antes de cambiar código, presentar diagnóstico, archivos afectados, riesgos y pruebas previstas.
4. Esperar autorización de Aurelio para cambios relevantes. Trabajar en rama separada y respaldar primero.
5. No rehacer consultas o módulos ya revisados, incluido Aguascalientes, sin defecto reproducible o instrucción explícita.
6. Probar entrada, cobro, consulta, salida y periféricos antes de instalar.
7. Documentar cada cambio: fecha, responsable, rama/commit, prueba, resultado y aprobación.
8. Nunca subir secretos, contraseñas ni datos de clientes a GitHub.
9. No desplegar automáticamente a equipos de producción.

## Pendientes inmediatos
- [ ] EST-01 Preguntar a Jorge dónde conserva su versión, cuál es la más reciente y dónde funciona. Respaldarla sin modificar.
- [ ] EST-02 Identificar y respaldar versión estable del sistema actual.
- [ ] EST-03 Comparar únicamente diferencias visuales de la TPV.
- [ ] EST-04 Aprobar e integrar mejoras seleccionadas en rama de trabajo.
- [ ] EST-05 Generar instalador Ubuntu y verificar instalación limpia.
- [ ] EST-06 Probar flujo completo en estacionamiento piloto y etiquetar versión estable.

## Bitácora de decisiones
- 2026-10-24: GitHub será la referencia del código y del estado del proyecto de estacionamientos.
- 2026-10-24: Prioridad: pantallas de Jorge e instalador; cajero, pagos digitales y elevador quedan en diseño.
- 2026-10-24: Los agentes primero inspeccionan e informan; no modifican sin autorización.

## Plantilla para actualizar después de cada sesión
Fecha:
Tarea/ID:
Versión o commit revisado:
Qué ya estaba hecho:
Qué se cambió:
Pruebas y resultado:
Pendientes:
Aprobado por:
