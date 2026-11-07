# Удаление колонки portal_email из старых попыток (в модели её нет, в БД могла остаться).
# Выполняется только для PostgreSQL: SQLite не поддерживает DROP COLUMN IF EXISTS (тесты).

from django.db import migrations, connection


def drop_portal_email_if_exists(apps, schema_editor):
    if connection.vendor == 'postgresql':
        schema_editor.execute('ALTER TABLE interns DROP COLUMN IF EXISTS portal_email;')


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0014_intern_corporate_email'),
    ]

    operations = [
        migrations.RunPython(drop_portal_email_if_exists, migrations.RunPython.noop),
    ]
