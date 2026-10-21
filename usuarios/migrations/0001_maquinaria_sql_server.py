import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(db_column='CategoriaID', primary_key=True, serialize=False)),
                ('nombre', models.CharField(db_column='Nombre', max_length=80, unique=True)),
                ('descripcion', models.CharField(blank=True, db_column='Descripcion', max_length=200, null=True)),
            ],
            options={'db_table': 'Categoria', 'ordering': ('nombre',)},
        ),
        migrations.CreateModel(
            name='Maquinaria',
            fields=[
                ('id', models.AutoField(db_column='EquipoID', primary_key=True, serialize=False)),
                ('codigo', models.CharField(db_column='Codigo', max_length=20, unique=True)),
                ('nombre', models.CharField(db_column='Nombre', max_length=120)),
                ('marca', models.CharField(blank=True, db_column='Marca', max_length=60, null=True)),
                ('modelo', models.CharField(blank=True, db_column='Modelo', max_length=60, null=True)),
                ('costo_adquisicion', models.DecimalField(db_column='CostoAdquisicion', decimal_places=2, max_digits=18, validators=[django.core.validators.MinValueValidator(0)])),
                ('tarifa_diaria', models.DecimalField(db_column='TarifaDiaria', decimal_places=2, max_digits=18, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('tarifa_semanal', models.DecimalField(db_column='TarifaSemanal', decimal_places=2, max_digits=18, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('tarifa_mensual', models.DecimalField(db_column='TarifaMensual', decimal_places=2, max_digits=18, validators=[django.core.validators.MinValueValidator(0.01)])),
                ('deposito_garantia', models.DecimalField(db_column='DepositoGarantia', decimal_places=2, default=0, max_digits=18, validators=[django.core.validators.MinValueValidator(0)])),
                ('activo', models.BooleanField(db_column='Activo', default=True)),
                ('categoria', models.ForeignKey(db_column='CategoriaID', on_delete=django.db.models.deletion.PROTECT, related_name='maquinarias', to='usuarios.categoria')),
            ],
            options={'db_table': 'Maquinaria', 'ordering': ('codigo',)},
        ),
        migrations.CreateModel(
            name='Unidad',
            fields=[
                ('id', models.AutoField(db_column='UnidadID', primary_key=True, serialize=False)),
                ('numero_serie', models.CharField(db_column='NumeroSerie', max_length=50, unique=True)),
                ('estado', models.CharField(choices=[('Disponible', 'Disponible'), ('Alquilado', 'Alquilado'), ('Mantenimiento', 'En mantenimiento'), ('Baja', 'Fuera de servicio')], db_column='Estado', default='Disponible', max_length=20)),
                ('horas_uso', models.DecimalField(db_column='HorasUso', decimal_places=1, default=0, max_digits=10, validators=[django.core.validators.MinValueValidator(0)])),
                ('fecha_adquisicion', models.DateField(blank=True, db_column='FechaAdquisicion', null=True)),
                ('activo', models.BooleanField(db_column='Activo', default=True)),
                ('ubicacion_actual', models.CharField(blank=True, db_column='UbicacionActual', max_length=200, null=True)),
                ('maquinaria', models.ForeignKey(db_column='EquipoID', on_delete=django.db.models.deletion.PROTECT, related_name='unidades', to='usuarios.maquinaria')),
            ],
            options={'db_table': 'Unidad', 'ordering': ('maquinaria__codigo', 'numero_serie')},
        ),
    ]
