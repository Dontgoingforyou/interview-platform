"""
Data-миграция: нормализация telegram_username, responsible_hr, hiring_hr.

- telegram_username: приводит к формату @username
  (принимает: username, @username, t.me/username, https://t.me/username).
- responsible_hr, hiring_hr: убирает ведущий символ "@" из имён HR.
"""
import re
from django.db import migrations


TELEGRAM_RE = re.compile(r'^@[a-zA-Z0-9_]{4,31}$')


def _normalize_telegram_username(value):
    """Копия interns.validators.normalize_telegram_username для изоляции миграции."""
    if not value:
        return value

    value = value.strip()

    if 't.me/' in value:
        value = '@' + value.split('t.me/')[-1].strip('/')

    if value and not value.startswith('@'):
        value = '@' + value

    return value


def normalize_fields(apps, schema_editor):
    Intern = apps.get_model('interns', 'Intern')
    to_update = []

    for intern in Intern.objects.all():
        changed = False

        if intern.telegram_username:
            normalized = _normalize_telegram_username(intern.telegram_username)
            if normalized != intern.telegram_username:
                intern.telegram_username = normalized
                changed = True

        for field in ('responsible_hr', 'hiring_hr'):
            val = getattr(intern, field) or ''
            if val.startswith('@'):
                setattr(intern, field, val.lstrip('@').strip())
                changed = True

        if changed:
            to_update.append(intern)

    if to_update:
        Intern.objects.bulk_update(to_update, ['telegram_username', 'responsible_hr', 'hiring_hr'])


def reverse_normalize(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0011_fk_direction'),
    ]

    operations = [
        migrations.RunPython(normalize_fields, reverse_normalize),
    ]
