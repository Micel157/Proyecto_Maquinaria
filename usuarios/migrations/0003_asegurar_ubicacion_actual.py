from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0002_integracion_y_restricciones')]

    operations = [
        migrations.RunSQL(
            sql='''
                IF COL_LENGTH(N'dbo.Unidad', N'UbicacionActual') IS NULL
                    ALTER TABLE [Unidad]
                    ADD [UbicacionActual] nvarchar(200) NULL;
            ''',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
