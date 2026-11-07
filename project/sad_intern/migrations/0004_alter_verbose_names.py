# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sad_intern', '0003_sadintern_manager_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sadintern',
            name='days_waiting',
            field=models.PositiveIntegerField(editable=False, verbose_name='Дней с нами'),
        ),
        migrations.AlterField(
            model_name='sadintern',
            name='waiting_since',
            field=models.DateField(help_text='Дата выхода на собеседования (real_interview_date). Показывает, сколько дней стажер у нас.', verbose_name='Ждет с'),
        ),
    ]
