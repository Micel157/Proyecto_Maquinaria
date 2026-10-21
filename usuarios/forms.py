from django import forms
from django.db import transaction

from .models import Categoria, Maquinaria, Unidad


class MaquinariaForm(forms.Form):
    ESTADOS = Unidad.ESTADOS

    codigo = forms.CharField(
        label='Código de catálogo',
        max_length=20,
        strip=True,
        help_text='Identificador único del modelo o tipo de maquinaria.',
    )
    nombre = forms.CharField(label='Nombre', max_length=120, strip=True)
    categoria = forms.CharField(
        label='Categoría',
        max_length=80,
        strip=True,
        help_text='Se reutiliza la categoría si ya existe.',
    )
    marca = forms.CharField(label='Marca', max_length=60, strip=True, required=False)
    modelo = forms.CharField(label='Modelo', max_length=60, strip=True, required=False)
    costo_adquisicion = forms.DecimalField(
        label='Costo de adquisición',
        max_digits=18,
        decimal_places=2,
        min_value=0,
    )
    tarifa_diaria = forms.DecimalField(
        label='Tarifa diaria',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    tarifa_semanal = forms.DecimalField(
        label='Tarifa semanal',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    tarifa_mensual = forms.DecimalField(
        label='Tarifa mensual',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    deposito_garantia = forms.DecimalField(
        label='Depósito de garantía',
        max_digits=18,
        decimal_places=2,
        min_value=0,
        initial=0,
    )
    numero_serie = forms.CharField(
        label='Número de serie',
        max_length=50,
        strip=True,
        help_text='Identifica de forma única la unidad física.',
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=ESTADOS,
        initial='Disponible',
    )
    horas_uso = forms.DecimalField(
        label='Horas de uso',
        max_digits=10,
        decimal_places=1,
        min_value=0,
        initial=0,
    )
    fecha_adquisicion = forms.DateField(
        label='Fecha de adquisición',
        required=False,
        input_formats=('%Y-%m-%d',),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if Maquinaria.objects.filter(codigo__iexact=codigo).exists():
            raise forms.ValidationError('Ya existe una maquinaria con este código.')
        return codigo

    def clean_numero_serie(self):
        numero_serie = self.cleaned_data['numero_serie']
        if Unidad.objects.filter(numero_serie__iexact=numero_serie).exists():
            raise forms.ValidationError(
                'Ya existe una maquinaria con este número de serie.'
            )
        return numero_serie

    @transaction.atomic
    def save(self):
        datos = self.cleaned_data
        categoria = Categoria.objects.filter(
            nombre__iexact=datos['categoria']
        ).first()
        if categoria is None:
            categoria = Categoria.objects.create(nombre=datos['categoria'])
        maquinaria = Maquinaria.objects.create(
            categoria=categoria,
            codigo=datos['codigo'],
            nombre=datos['nombre'],
            marca=datos['marca'] or None,
            modelo=datos['modelo'] or None,
            costo_adquisicion=datos['costo_adquisicion'],
            tarifa_diaria=datos['tarifa_diaria'],
            tarifa_semanal=datos['tarifa_semanal'],
            tarifa_mensual=datos['tarifa_mensual'],
            deposito_garantia=datos['deposito_garantia'],
        )
        return Unidad.objects.create(
            maquinaria=maquinaria,
            numero_serie=datos['numero_serie'],
            estado=datos['estado'],
            horas_uso=datos['horas_uso'],
            fecha_adquisicion=datos['fecha_adquisicion'],
        )
