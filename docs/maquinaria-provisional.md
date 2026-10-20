# HU-02 y HU-03: implementación provisional de maquinaria

El registro, listado, filtros y detalle de maquinaria son una preparación para el
Sprint 2. Las rutas requieren una sesión iniciada y usan el login existente.

## Almacenamiento de demostración

Los registros se guardan en `data/maquinaria_provisional.json` (relativo a la
carpeta del proyecto), no en `db.sqlite3` ni en SQL Server. Se puede cambiar la
ruta con el ajuste Django `MAQUINARIA_DATA_FILE`. No usar este almacenamiento
local como persistencia de producción ni como almacén multiusuario concurrente.

## Campos provisionales

El formulario agrupa datos tentativos de catálogo (código, nombre, categoría,
marca, modelo, costo, tarifas y depósito) y de unidad física (número de serie,
estado, horas y fecha de adquisición). La separación es una hipótesis de trabajo
basada en la copia SQL recuperada (`Equipo`/`Unidad`), no una decisión sobre el
esquema definitivo. La categoría es texto libre en este prototipo. Los límites,
obligatoriedad, valores de estado, unicidad y correspondencia de todos los
campos deben revisarse cuando se reciba y valide el script actualizado.

No se añadieron modelos, migraciones ni tablas, ni se cambió la configuración de
la base de datos. La integración pendiente consiste en acordar el modelo final,
conectar las claves y catálogos (por ejemplo la categoría), mover la lectura y
escritura a SQL Server y ejecutar sus validaciones de integridad.
