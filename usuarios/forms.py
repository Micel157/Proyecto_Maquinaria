from django import forms

from .maquinaria_store import obtener_maquinarias


class MaquinariaForm(forms.Form):
    ESTADOS = (
        ('Disponible', 'Disponible'),
        ('Alquilado', 'Alquilado'),
        ('Mantenimiento', 'En mantenimiento'),
        ('Baja', 'Fuera de servicio'),
    )

    codigo = forms.CharField(
        label='Código de catálogo (provisional)',
        max_length=20,
        strip=True,
        help_text='Identificador temporal del modelo o tipo de maquinaria.',
    )
    nombre = forms.CharField(label='Nombre', max_length=120, strip=True)
    categoria = forms.CharField(
        label='Categoría (provisional)',
        max_length=80,
        strip=True,
        help_text='Texto temporal; falta confirmar si se elegirá de un catálogo.',
    )
    marca = forms.CharField(label='Marca', max_length=60, strip=True, required=False)
    modelo = forms.CharField(label='Modelo', max_length=60, strip=True, required=False)
    costo_adquisicion = forms.DecimalField(
        label='Costo de adquisición (provisional)',
        max_digits=18,
        decimal_places=2,
        min_value=0,
    )
    tarifa_diaria = forms.DecimalField(
        label='Tarifa diaria (provisional)',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    tarifa_semanal = forms.DecimalField(
        label='Tarifa semanal (provisional)',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    tarifa_mensual = forms.DecimalField(
        label='Tarifa mensual (provisional)',
        max_digits=18,
        decimal_places=2,
        min_value=0.01,
    )
    deposito_garantia = forms.DecimalField(
        label='Depósito de garantía (provisional)',
        max_digits=18,
        decimal_places=2,
        min_value=0,
        initial=0,
    )
    numero_serie = forms.CharField(
        label='Número de serie (provisional)',
        max_length=50,
        strip=True,
        help_text='Identifica la unidad física; falta confirmar la regla de unicidad.',
    )
    estado = forms.ChoiceField(
        label='Estado (provisional)',
        choices=ESTADOS,
        initial='Disponible',
    )
    horas_uso = forms.DecimalField(
        label='Horas de uso (provisional)',
        max_digits=10,
        decimal_places=1,
        min_value=0,
        initial=0,
    )
    fecha_adquisicion = forms.DateField(
        label='Fecha de adquisición (provisional)',
        required=False,
        input_formats=('%Y-%m-%d',),
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']
        if any(
            item['codigo'].casefold() == codigo.casefold()
            for item in obtener_maquinarias()
        ):
            raise forms.ValidationError('Ya existe una maquinaria con este código.')
        return codigo

    def clean_numero_serie(self):
        numero_serie = self.cleaned_data['numero_serie']
        if any(
            item['numero_serie'].casefold() == numero_serie.casefold()
            for item in obtener_maquinarias()
        ):
            raise forms.ValidationError(
                'Ya existe una maquinaria con este número de serie.'
            )
        return numero_serie
