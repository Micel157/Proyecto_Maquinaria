"""Genera o completa la configuración local privada de desarrollo."""
import json
import secrets
import tempfile
from pathlib import Path


def main():
    raiz = Path(__file__).resolve().parent.parent
    destino = raiz / 'config.local.json'
    ejemplo = raiz / 'config.local.example.json'
    ejemplo_config = json.loads(ejemplo.read_text(encoding='utf-8'))
    if destino.exists():
        configuracion = json.loads(destino.read_text(encoding='utf-8'))
        mensaje = 'config.local.json completado sin cambiar secretos existentes.'
    else:
        configuracion = {}
        mensaje = 'config.local.json creado con una clave privada para este equipo.'

    configuracion.setdefault('SECRET_KEY', secrets.token_urlsafe(64))
    configuracion.setdefault('DEBUG', ejemplo_config['DEBUG'])
    configuracion.setdefault('ALLOWED_HOSTS', ejemplo_config['ALLOWED_HOSTS'])
    configuracion.setdefault('DATABASE', ejemplo_config['DATABASE'])

    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode='w',
        encoding='utf-8',
        dir=destino.parent,
        prefix=f'.{destino.name}.',
        suffix='.tmp',
        delete=False,
    ) as archivo:
        json.dump(configuracion, archivo, indent=2)
        archivo.write('\n')
        temporal = Path(archivo.name)
    temporal.replace(destino)
    print(mensaje)


if __name__ == '__main__':
    main()
