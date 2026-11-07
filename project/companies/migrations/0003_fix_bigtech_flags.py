from django.db import migrations

from core.constants import COMPANY_OPTIONS


def fix_bigtech_flags(apps, schema_editor):
    """Сбрасывает is_bigtech у всех компаний, затем выставляет только тем,
    чьё название совпадает с каноничными именами из COMPANY_OPTIONS."""
    Company = apps.get_model('companies', 'Company')
    Company.objects.all().update(is_bigtech=False)
    bigtech_names = list(COMPANY_OPTIONS.keys())
    Company.objects.filter(name__in=bigtech_names).update(is_bigtech=True)


def reverse_fix(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_add_aliases_to_company'),
    ]

    operations = [
        migrations.RunPython(fix_bigtech_flags, reverse_fix),
    ]
