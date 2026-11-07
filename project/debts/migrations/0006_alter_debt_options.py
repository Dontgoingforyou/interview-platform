from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('debts', '0005_fk_direction'),
    ]
    operations = [
        migrations.AlterModelOptions(
            name='debt',
            options={
                'ordering': ['id'],
                'verbose_name': 'Долг',
                'verbose_name_plural': 'Долги',
            },
        ),
    ]
