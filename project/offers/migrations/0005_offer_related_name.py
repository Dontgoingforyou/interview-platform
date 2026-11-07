# Generated manually — related_name только в метаданных ORM, схема БД не меняется

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directions', '0001_initial'),
        ('interns', '0006_intern_real_interview_date'),
        ('offers', '0004_fk_direction'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offer',
            name='intern',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='offers',
                to='interns.intern',
                verbose_name='Студент',
            ),
        ),
        migrations.AlterField(
            model_name='offer',
            name='direction',
            field=models.ForeignKey(
                db_index=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='offers',
                to='directions.direction',
                verbose_name='Направление',
            ),
        ),
    ]
