# Revisión del script SQL original

El archivo original `C:\Users\jorgu\Downloads\Script alquiler de maquinaria`
se conservó sin cambios. El análisis se hizo contra SHA-256
`0792FE979994F5BD43DB9A79BE49D4F60C3F2F8...` y contra la instancia local
`Thechosenone\SQLEXPRESS` antes de ejecutar migraciones.

## Hallazgos

- El script crea `dbo.Maquinaria`, pero las funciones, vistas y procedimientos
  consultan `dbo.Equipo`. Ese objeto no existe.
- Usa `dbo.Parametro` y `dbo.AlquilerDetalle`, pero no los crea.
- Intenta crear funciones y vistas antes de crear las tablas de las que dependen.
  Por eso una ejecución limpia deja esos objetos sin crear aunque las tablas
  posteriores sí lleguen a existir.
- La ruta de los archivos MDF/LDF está fijada a una instancia
  `MSSQL16.MSSQLSERVER`; no sirve para `SQLEXPRESS` ni para otros equipos.
- El script cambia muchas opciones de toda la base y usa nivel de compatibilidad
  160. La aplicación no necesita esos cambios globales.
- La nomenclatura mezcla `EquipoID`, `Maquinaria`, `IdRepuesto` y otros estilos.
  Se conserva `EquipoID` en las tres tablas ya existentes para no romper datos,
  mientras Django presenta los nombres coherentes `categoria`, `maquinaria` y
  `unidad`.

La base local encontrada estaba en línea y sin filas en las tablas de negocio.
Contenía `Parametro` y el campo adicional `Unidad.UbicacionActual`, pero no
`AlquilerDetalle`, vistas, funciones ni procedimientos del archivo original.

## Orden corregido

Para una instalación nueva, las migraciones de Django crean primero las tablas
del módulo implementado y después sus restricciones. Para completar en el futuro
el flujo de alquiler del script original, el orden debe ser:

1. tablas base (`Categoria`, `Maquinaria`, `Unidad`, `Cliente`, `Alquiler` y
   `Parametro`);
2. tabla puente `AlquilerDetalle` y sus claves foráneas;
3. tipos de tabla;
4. funciones;
5. vistas;
6. procedimientos almacenados.

`sql/01_completar_esquema_legacy.sql` aplica de forma aditiva las correcciones
de tablas, nombres y dependencias. `sql/02_procedimientos_legacy_corregidos.sql`
conserva los ocho procedimientos del original, cambia `Equipo` por `Maquinaria`
y permite repetir su compilación con `CREATE OR ALTER`. Ninguno elimina ni
sustituye datos. Antes de usar el flujo de alquiler hay que definir los valores
de `Parametro` (por ejemplo, ITBIS y recargo por mora) y cubrir esas historias
de usuario desde Django.
