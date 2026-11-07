from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0026_add_city_and_url_max_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='intern',
            name='keycloak_id',
        ),
    ]
