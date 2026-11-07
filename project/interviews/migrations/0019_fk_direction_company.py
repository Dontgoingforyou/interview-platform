"""
Миграция: IntegerField direction_id/company_id → ForeignKey в Interview.

Использует SeparateDatabaseAndState:
- state_operations: обновляет Django-модель (удаляет IntegerField, добавляет FK)
- database_operations: добавляет FK-constraints на существующие колонки только для PostgreSQL

ВАЖНО: запускать только ПОСЛЕ migrate_external_to_local, чтобы все direction_id/company_id
имели соответствующие записи в directions_direction и companies_company.
"""
import django.db.models.deletion
from django.db import migrations, models


def add_fk_constraints(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(
        "ALTER TABLE interviews "
        "ADD CONSTRAINT fk_interview_direction "
        "FOREIGN KEY (direction_id) REFERENCES directions_direction(id) "
        "NOT VALID DEFERRABLE INITIALLY DEFERRED;"
    )
    schema_editor.execute(
        "ALTER TABLE interviews "
        "ADD CONSTRAINT fk_interview_company "
        "FOREIGN KEY (company_id) REFERENCES companies_company(id) "
        "NOT VALID DEFERRABLE INITIALLY DEFERRED;"
    )


def remove_fk_constraints(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS fk_interview_direction;")
    schema_editor.execute("ALTER TABLE interviews DROP CONSTRAINT IF EXISTS fk_interview_company;")


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('directions', '0001_initial'),
        ('interviews', '0018_company'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='interview',
                    name='direction_id',
                ),
                migrations.RemoveField(
                    model_name='interview',
                    name='company_id',
                ),
                migrations.AddField(
                    model_name='interview',
                    name='direction',
                    field=models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='directions.direction',
                        verbose_name='Направление',
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name='interview',
                    name='company',
                    field=models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='companies.company',
                        verbose_name='Компания',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_fk_constraints, remove_fk_constraints),
            ],
        ),
    ]
