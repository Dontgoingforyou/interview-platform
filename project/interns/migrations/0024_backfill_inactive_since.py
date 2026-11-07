# Generated manually: заполнение inactive_since для уже неактивных стажёров

from django.db import migrations
from django.utils import timezone


def backfill_inactive_since(apps, schema_editor):
    Intern = apps.get_model('interns', 'Intern')
    now = timezone.now()
    Intern.objects.filter(
        manual_status__in=('ушел', 'оффер'),
        inactive_since__isnull=True,
    ).update(inactive_since=now)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0023_add_intern_inactive_since'),
    ]

    operations = [
        migrations.RunPython(backfill_inactive_since, noop),
    ]
