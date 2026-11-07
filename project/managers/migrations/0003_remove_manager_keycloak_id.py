from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('managers', '0002_add_hidden_at_to_manager'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='manager',
            name='keycloak_id',
        ),
    ]
