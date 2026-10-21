# Sistema de alquiler de equipos

Proyecto Django con inicio de sesión, panel por rol, registro y consulta de
maquinaria. La aplicación usa SQL Server para cuentas, roles, sesiones, catálogo
y unidades físicas.

## Requisitos

- Python 3.12 a 3.14 (este entorno usa Python 3.14).
- SQL Server 2017 o posterior; se probó con SQL Server 2025 Express.
- Microsoft ODBC Driver 18 for SQL Server.
- PowerShell y Git en Windows.

El backend `mssql-django==2.0.0` soporta Django 6.1 y Python 3.14.

## Instalación

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/configurar_desarrollo.py
```

El último comando crea o completa `config.local.json` sin cambiar secretos ya
existentes. Ese archivo está excluido de Git. La configuración de ejemplo usa
autenticación integrada de Windows contra `localhost\SQLEXPRESS` y la base
`AlquilerEquipos`:

```json
"DATABASE": {
  "ENGINE": "mssql",
  "NAME": "AlquilerEquipos",
  "HOST": "localhost\\SQLEXPRESS",
  "PORT": "",
  "USER": "",
  "PASSWORD": "",
  "OPTIONS": {
    "driver": "ODBC Driver 18 for SQL Server",
    "extra_params": "TrustServerCertificate=yes"
  }
}
```

Para autenticación SQL, escribe `USER` y `PASSWORD` solo en
`config.local.json`. También se admiten las variables `DJANGO_DB_ENGINE`,
`DJANGO_DB_NAME`, `DJANGO_DB_HOST`, `DJANGO_DB_PORT`, `DJANGO_DB_USER`,
`DJANGO_DB_PASSWORD`, `DJANGO_DB_DRIVER` y `DJANGO_DB_EXTRA_PARAMS`.

## Preparar SQL Server

Crea una base vacía si todavía no existe:

```sql
CREATE DATABASE [AlquilerEquipos];
```

Antes de cambiar una base existente, ejecuta el inventario de solo lectura:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -C -i sql\00_inspeccionar_base.sql
```

Haz una copia desde SQL Server Management Studio o con `BACKUP DATABASE`. No
guardes archivos `.bak` en Git. Después aplica las migraciones. `--fake-initial`
reconoce `Categoria`, `Maquinaria` y `Unidad` si ya venían del script original;
en una base nueva las crea.

```powershell
.\.venv\Scripts\python.exe manage.py migrate --fake-initial
```

Las migraciones de Django son la fuente de verdad para el módulo implementado.
Los archivos siguientes conservan y corrigen por separado los objetos futuros
del script del compañero:

- `sql/01_completar_esquema_legacy.sql`: crea los objetos omitidos y corrige
  referencias de `Equipo` a `Maquinaria`.
- `sql/02_procedimientos_legacy_corregidos.sql`: procedimientos derivados del
  original con nombres corregidos y `CREATE OR ALTER`.
- `docs/revision-script-original.md`: hallazgos, diferencias y orden correcto.

Los scripts son aditivos. No eliminan ni reemplazan filas. El módulo web actual
no depende de los procedimientos de alquiler.

## Migrar datos locales anteriores

Conserva `db.sqlite3` y `data/maquinaria_provisional.json` como respaldo. Con la
conexión SQL Server activa, ejecuta:

```powershell
.\.venv\Scripts\python.exe manage.py migrar_datos_locales
```

El comando:

- copia usuarios sin recalcular sus contraseñas: conserva exactamente el hash;
- copia grupos, membresías y permisos compatibles;
- convierte el JSON en `Categoria`, `Maquinaria` y `Unidad`;
- no actualiza usuarios, códigos o números de serie que ya existan;
- verifica al final que usuarios, hashes, roles y unidades estén presentes;
- se puede repetir sin duplicar datos.

Se pueden indicar rutas distintas con `--sqlite` y `--json`.

## Roles y acceso

| Rol | Consultar, filtrar y ver detalles | Registrar | Django Admin |
| --- | --- | --- | --- |
| Administrador (`is_superuser`) | Sí | Sí | Sí |
| Supervisor (grupo `Supervisor`) | Sí | No | No |
| Sin rol | No | No | No |

La vista de registro comprueba el rol en el servidor. Un Supervisor recibe HTTP
403 aunque escriba directamente `/maquinaria/registrar/` o envíe un POST.

Para crear cuentas nuevas:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py crear_supervisor luis --nombre "Luis"
.\.venv\Scripts\python.exe manage.py changepassword luis
```

## Comprobar y ejecutar

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test usuarios
.\.venv\Scripts\python.exe manage.py runserver
```

Abre <http://127.0.0.1:8000/login/>. El administrador de Django está en
<http://127.0.0.1:8000/admin/>.

Las pruebas usan una base temporal `test_AlquilerEquipos` en la misma instancia
SQL Server y la eliminan al terminar. La cuenta configurada debe poder crear y
eliminar esa base de prueba.

## Archivos locales y Git

`.gitignore` excluye `config.local.json`, `.env`, claves, SQLite, `data/`,
respaldos, copias SQL originales, `tmp/`, `output/`, el entorno virtual y cachés.
No uses `git add -f` con esos archivos.

Antes de compartir cambios:

```powershell
git status --short
git diff --cached --stat
git diff --cached
```

Trabaja en una rama y usa un pull request para no sobrescribir cambios de otras
personas. Repositorio: <https://github.com/giorgioRD/Alquiler_maquinaria>.
