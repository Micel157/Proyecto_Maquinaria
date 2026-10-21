"""Capa de compatibilidad para código anterior que usaba almacenamiento JSON."""

from django.db import transaction

from .models import Categoria, Maquinaria, Unidad


def obtener_maquinarias():
    return Unidad.objects.select_related('maquinaria__categoria').all()


def obtener_maquinaria(maquinaria_id):
    return obtener_maquinarias().filter(pk=maquinaria_id).first()


@transaction.atomic
def crear_maquinaria(datos):
    categoria = Categoria.objects.filter(
        nombre__iexact=datos['categoria']
    ).first() or Categoria.objects.create(nombre=datos['categoria'])
    maquinaria = Maquinaria.objects.create(
        categoria=categoria,
        **{
            campo: datos[campo]
            for campo in (
                'codigo', 'nombre', 'marca', 'modelo', 'costo_adquisicion',
                'tarifa_diaria', 'tarifa_semanal', 'tarifa_mensual',
                'deposito_garantia',
            )
        },
    )
    return Unidad.objects.create(
        maquinaria=maquinaria,
        **{
            campo: datos[campo]
            for campo in ('numero_serie', 'estado', 'horas_uso', 'fecha_adquisicion')
        },
    )
