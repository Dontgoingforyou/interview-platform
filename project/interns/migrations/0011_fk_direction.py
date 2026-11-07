"""
Миграция: IntegerField direction_id → ForeignKey в Intern.

Использует SeparateDatabaseAndState: колонка direction_id уже существует,
добавляем FK-constraint только для PostgreSQL (SQLite не поддерживает ADD CONSTRAINT).

ВАЖНО: запускать только ПОСЛЕ migrate_external_to_local.
"""
import django.db.models.deletion
from django.db import migrations, models


def add_fk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(
        "ALTER TABLE interns "
        "ADD CONSTRAINT fk_intern_direction "
        "FOREIGN KEY (direction_id) REFERENCES directions_direction(id) "
        "NOT VALID DEFERRABLE INITIALLY DEFERRED;"
    )


def remove_fk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("ALTER TABLE interns DROP CONSTRAINT IF EXISTS fk_intern_direction;")


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0001_initial'),
        ('interns', '0010_remove_manager_id'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='intern',
                    name='direction_id',
                ),
                migrations.AddField(
                    model_name='intern',
                    name='direction',
                    field=models.ForeignKey(
                        db_index=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to='directions.direction',
                        verbose_name='Направление',
                    ),
                    preserve_default=False,
                ),
            ],
            database_operations=[
                migrations.RunPython(add_fk_constraint, remove_fk_constraint),
            ],
        ),
    ]
