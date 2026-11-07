# Generated manually to make direction_id nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0002_alter_debt_act_date_alter_debt_direction_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='debt',
            name='direction_id',
            field=models.IntegerField(blank=True, db_index=True, null=True, verbose_name='Направление (ID)'),
        ),
    ]
