# Sistema de alquiler de equipos

Proyecto Django para iniciar sesión, mostrar un panel según el rol y consultar
o registrar maquinaria. Preparado para desarrollo local y colaboración en un
repositorio privado. No es una configuración de despliegue de producción.

## Estado del almacenamiento

- **SQLite** (`db.sqlite3`): usuarios, grupos, sesiones y tablas internas de Django.
- **JSON provisional** (`data/maquinaria_provisional.json`): catálogo de maquinaria.
  Se crea al registrar el primer equipo; un clon nuevo empieza sin maquinaria.
  No es un almacén adecuado para escrituras concurrentes ni para producción.
- **SQL Server pendiente de integración**: todavía no se usa desde Django.
  Falta validar el esquema definitivo, configurar la conexión y sustituir el
  almacenamiento provisional. No se necesita SQL Server ni un controlador ODBC
  para ejecutar esta versión. Las copias SQL recuperadas se conservan localmente
  y se excluyen de Git hasta su revisión.

Más contexto en [docs/maquinaria-provisional.md](docs/maquinaria-provisional.md).

## Requisitos

- Python 3.12 o superior (entorno actual probado: Python 3.14).
- Git para clonar y compartir cambios.
- PowerShell en Windows para los comandos siguientes. En Linux/macOS usa
  `python3 -m venv .venv` y `.venv/bin/python` en lugar del ejecutable de Windows.

Las versiones de `requirements.txt` corresponden al entorno del proyecto;
incluyen Django y sus dependencias actuales, sin herramientas de generación de
documentos ni dependencias de SQL Server.

## Instalar y configurar

Tras clonar el repositorio privado y entrar en su carpeta, ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/configurar_desarrollo.py
.\.venv\Scripts\python.exe manage.py migrate
```

Si ya tienes un entorno `.venv`, no necesitas volver a crearlo.
El script genera `config.local.json` desde `config.local.example.json`, con una
clave secreta aleatoria propia de tu equipo. Si el archivo existe, lo conserva.
El ejemplo se comparte; la configuración privada está excluida de Git.
No pongas contraseñas ni claves reales en el ejemplo o en `settings.py`.

También se admiten variables de entorno, con prioridad sobre el archivo local:

| Variable | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave secreta privada; obligatoria si no hay una en la configuración local. |
| `DJANGO_DEBUG` | `true`, `1` o `yes` para desarrollo; `false` para desactivar depuración. |
| `DJANGO_ALLOWED_HOSTS` | Nombres de host separados por comas, por ejemplo `localhost,127.0.0.1`. |

Sin configuración local, `DEBUG` queda desactivado. No se cargan archivos `.env`
automáticamente: usa el JSON local o variables de entorno del proceso.

## Crear cuentas independientes

Cada compañero crea sus cuentas en su base local. Las cuentas y contraseñas no
viajan en Git, y no se incluyen credenciales predeterminadas.

Para crear el administrador, sigue las preguntas de Django:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

Para crear un supervisor llamado `luis`, mostrar el nombre Luis y asignarle una
contraseña de forma interactiva:

```powershell
.\.venv\Scripts\python.exe manage.py crear_supervisor luis --nombre "Luis"
.\.venv\Scripts\python.exe manage.py changepassword luis
```

`crear_supervisor` crea o asigna la cuenta al grupo `Supervisor`, sin permisos de
superusuario ni acceso a Django Admin. Repetirlo conserva su contraseña. Si el
nombre pertenece a una cuenta administrativa, rechaza la operación. En este
equipo la cuenta existente ya se llama `luis`; no necesitas crear otra ni cambiar
su contraseña para preparar el repositorio.

| Rol | Consultar y filtrar maquinaria / ver detalles | Registrar | Django Admin |
| --- | --- | --- | --- |
| Administrador | Sí | Sí | Sí |
| Supervisor | Sí | No | No |
| Sin rol asignado | No | No | No |

Ambas cuentas usan `/login/` y acceden a `/dashboard/`, donde aparecen su nombre
y rol. Más detalles en [docs/cuentas-y-roles.md](docs/cuentas-y-roles.md).

## Ejecutar y comprobar

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test usuarios
.\.venv\Scripts\python.exe manage.py runserver
```

Abre <http://127.0.0.1:8000/login/>. El administrador de Django está en
<http://127.0.0.1:8000/admin/> y requiere una cuenta administrativa.
El servidor de desarrollo se detiene con `Ctrl+C`.

## Archivos que se comparten

Se versionan `manage.py`, `config/`, `usuarios/` (incluidas sus migraciones,
plantillas, CSS y pruebas), `scripts/`, `docs/`, `requirements.txt`, este README,
`.gitignore` y `config.local.example.json`.

`.gitignore` excluye `.venv`, cachés, `.env` y sus variantes privadas, claves y
credenciales habituales, `config.local.json`, SQLite, `data/`, `tmp/`, `output/`,
respaldos y copias SQL recuperadas. La exclusión no borra los archivos locales.
No uses `git add -f` para incluir estos archivos. Si más adelante se añade un
esquema SQL revisado y sin datos sensibles, debe guardarse con una ruta y una
política de versionado explícitas.

Antes de cada commit, revisa:

```powershell
git status --short
git diff --cached --stat
git diff --cached
```

El `.gitignore` no protege secretos que ya estuvieran en el historial. Si alguna
vez se publica una clave, debe sustituirse y revisarse ese historial.

## Repositorio del equipo

Repositorio: <https://github.com/giorgioRD/Alquiler_maquinaria>.
Para descargarlo, necesitas acceso concedido por su propietario y autenticarte
en GitHub. Después ejecuta:

```powershell
git clone https://github.com/giorgioRD/Alquiler_maquinaria.git
cd Alquiler_maquinaria
```

Sigue las instrucciones de instalación y creación de cuentas anteriores. Para
compartir trabajo, crea una rama y revisa siempre los archivos del commit:

```powershell
git switch -c mi-cambio
git add .
git diff --cached --stat
git diff --cached
git commit -m "Describir el cambio realizado"
git push -u origin mi-cambio
```

Abre un pull request para revisar y combinar el cambio con `main`. El propietario
debe mantener el repositorio privado e invitar a sus compañeros. Cada uno deberá
generar su configuración y sus cuentas locales. No compartas tu `db.sqlite3` ni
tu configuración privada.
