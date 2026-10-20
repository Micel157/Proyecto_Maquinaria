"""Genera configuración local privada sin sobrescribir un archivo existente."""
import json
import secrets
from pathlib import Path


def main():
    raiz = Path(__file__).resolve().parent.parent
    destino = raiz / 'config.local.json'
    ejemplo = raiz / 'config.local.example.json'
    configuracion = json.loads(ejemplo.read_text(encoding='utf-8'))
    configuracion['SECRET_KEY'] = secrets.token_urlsafe(64)
    try:
        with destino.open('x', encoding='utf-8') as archivo:
            json.dump(configuracion, archivo, indent=2)
            archivo.write('\n')
    except FileExistsError:
        print('config.local.json ya existe. Se conserva sin cambios.')
    else:
        print('config.local.json creado con una clave privada para este equipo.')


if __name__ == '__main__':
    main()
