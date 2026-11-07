"""
Пустая миграция-заглушка. Модель Company перенесена в приложение companies.
Таблица companies_company создаётся миграцией companies/0001_initial.py.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0017_remove_hr_model'),
    ]

    operations = []
