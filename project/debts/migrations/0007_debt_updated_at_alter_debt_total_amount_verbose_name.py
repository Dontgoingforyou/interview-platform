import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('debts', '0006_alter_debt_options'),
    ]
    operations = [
        migrations.AddField(
            model_name='debt',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата обновления'),
        ),
        migrations.AlterField(
            model_name='debt',
            name='total_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                editable=False,
                max_digits=12,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name='Общая сумма',
            ),
        ),
    ]
