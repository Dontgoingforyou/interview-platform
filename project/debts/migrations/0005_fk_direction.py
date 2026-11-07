"""
Миграция: IntegerField direction_id → ForeignKey (nullable) в Debt.

Использует SeparateDatabaseAndState: колонка direction_id уже существует,
добавляем FK-constraint только для PostgreSQL.

ВАЖНО: запускать только ПОСЛЕ migrate_external_to_local.
"""
import django.db.models.deletion
from django.db import migrations, models


def add_fk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(
        "ALTER TABLE debts "
        "ADD CONSTRAINT fk_debt_direction "
        "FOREIGN KEY (direction_id) REFERENCES directions_direction(id) "
        "NOT VALID DEFERRABLE INITIALLY DEFERRED;"
    )


def remove_fk_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute("ALTER TABLE debts DROP CONSTRAINT IF EXISTS fk_debt_direction;")


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0001_initial'),
        ('debts', '0004_alter_debt_paid_amount_alter_debt_total_amount_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='debt',
                    name='direction_id',
                ),
                migrations.AddField(
                    model_name='debt',
                    name='direction',
                    field=models.ForeignKey(
                        blank=True,
                        db_index=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to='directions.direction',
                        verbose_name='Направление',
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_fk_constraint, remove_fk_constraint),
            ],
        ),
    ]
