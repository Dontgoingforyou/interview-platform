from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0012_normalize_tg_and_hr_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='intern',
            name='keycloak_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                unique=True,
                verbose_name='Keycloak ID',
            ),
        ),
    ]
