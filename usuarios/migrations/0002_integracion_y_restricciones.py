from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0001_maquinaria_sql_server')]

    operations = [
        migrations.AddField(
            model_name='unidad',
            name='identificador_legacy',
            field=models.UUIDField(blank=True, db_column='IdentificadorLegacy', null=True, unique=True),
        ),
        migrations.AddConstraint(
            model_name='maquinaria',
            constraint=models.CheckConstraint(condition=models.Q(('costo_adquisicion__gte', 0)), name='CK_Maquinaria_Costo_NoNegativo'),
        ),
        migrations.AddConstraint(
            model_name='maquinaria',
            constraint=models.CheckConstraint(condition=models.Q(('tarifa_diaria__gt', 0)), name='CK_Maquinaria_TarifaDiaria_Positiva'),
        ),
        migrations.AddConstraint(
            model_name='maquinaria',
            constraint=models.CheckConstraint(condition=models.Q(('tarifa_semanal__gt', 0)), name='CK_Maquinaria_TarifaSemanal_Positiva'),
        ),
        migrations.AddConstraint(
            model_name='maquinaria',
            constraint=models.CheckConstraint(condition=models.Q(('tarifa_mensual__gt', 0)), name='CK_Maquinaria_TarifaMensual_Positiva'),
        ),
        migrations.AddConstraint(
            model_name='maquinaria',
            constraint=models.CheckConstraint(condition=models.Q(('deposito_garantia__gte', 0)), name='CK_Maquinaria_Deposito_NoNegativo'),
        ),
        migrations.AddConstraint(
            model_name='unidad',
            constraint=models.CheckConstraint(condition=models.Q(('estado__in', ['Disponible', 'Alquilado', 'Mantenimiento', 'Baja'])), name='CK_Unidad_Estado_Valido'),
        ),
        migrations.AddConstraint(
            model_name='unidad',
            constraint=models.CheckConstraint(condition=models.Q(('horas_uso__gte', 0)), name='CK_Unidad_Horas_NoNegativas'),
        ),
    ]
