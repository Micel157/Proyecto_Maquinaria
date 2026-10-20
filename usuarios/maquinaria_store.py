import json
import os
import tempfile
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

from django.conf import settings


def _archivo_datos():
    return Path(
        getattr(
            settings,
            'MAQUINARIA_DATA_FILE',
            settings.BASE_DIR / 'data' / 'maquinaria_provisional.json',
        )
    )


def obtener_maquinarias():
    archivo = _archivo_datos()
    if not archivo.exists():
        return []
    with archivo.open(encoding='utf-8') as datos:
        return json.load(datos)


def obtener_maquinaria(maquinaria_id):
    return next(
        (
            maquinaria
            for maquinaria in obtener_maquinarias()
            if maquinaria['id'] == maquinaria_id
        ),
        None,
    )


def crear_maquinaria(datos):
    maquinarias = obtener_maquinarias()
    maquinaria = {
        clave: (
            valor.isoformat()
            if isinstance(valor, date)
            else str(valor)
            if isinstance(valor, Decimal)
            else valor
        )
        for clave, valor in datos.items()
    }
    maquinaria['id'] = str(uuid.uuid4())
    maquinarias.append(maquinaria)

    archivo = _archivo_datos()
    archivo.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporal = tempfile.mkstemp(
        dir=archivo.parent,
        prefix=f'.{archivo.name}.',
        suffix='.tmp',
    )
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as salida:
            json.dump(maquinarias, salida, ensure_ascii=False, indent=2)
            salida.write('\n')
        os.replace(temporal, archivo)
    finally:
        if os.path.exists(temporal):
            os.unlink(temporal)
    return maquinaria
