# Generated manually for audit refactor

import django.utils.timezone
from django.db import migrations, models
from django.db.models import deletion


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge_base_app', '0001_add_kb_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='kbsection',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kbsection',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата изменения'),
        ),
        migrations.AddField(
            model_name='kbarticle',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Дата создания'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kbarticle',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата изменения'),
        ),
        migrations.AlterField(
            model_name='kbarticle',
            name='section',
            field=models.ForeignKey(
                db_index=True,
                on_delete=deletion.CASCADE,
                related_name='articles',
                to='knowledge_base_app.kbsection',
                verbose_name='Раздел',
            ),
        ),
    ]
