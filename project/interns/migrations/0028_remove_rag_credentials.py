from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0027_remove_intern_keycloak_id'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InternRAGCredentials',
        ),
        migrations.AlterField(
            model_name='intern',
            name='corporate_email',
            field=models.EmailField(
                blank=True,
                db_index=True,
                help_text='Заполняется при первой привязке по ФИО и используется для входа на портал.',
                max_length=254,
                null=True,
                verbose_name='Почта входа на портал',
            ),
        ),
    ]
