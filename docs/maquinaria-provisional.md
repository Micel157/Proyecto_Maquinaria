# HU-02 y HU-03: traslado del prototipo de maquinaria

El registro, listado, filtros y detalle comenzaron con almacenamiento local en
`data/maquinaria_provisional.json`. Ese archivo se conserva como origen y
respaldo local, pero la aplicación ya lee y escribe en SQL Server.

El modelo definitivo para estas historias separa:

- `Categoria`: catálogo reutilizable;
- `Maquinaria`: código, nombre, marca, modelo, costo, tarifas y depósito;
- `Unidad`: número de serie, estado, horas, fecha de adquisición y ubicación.

La relación conserva `Maquinaria.EquipoID` y `Unidad.EquipoID` para ser
compatible con la base encontrada. Django expone nombres coherentes en Python.
Código y número de serie son únicos, los importes y horas no pueden ser
negativos y las tarifas deben ser positivas.

`python manage.py migrar_datos_locales` transforma el JSON anterior de forma
aditiva. El comando no reemplaza registros existentes y verifica cada unidad al
terminar. Consulta el procedimiento completo en el README y el análisis del SQL
recibido en `docs/revision-script-original.md`.
