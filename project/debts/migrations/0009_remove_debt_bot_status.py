from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('debts', '0008_performance_indexes'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='debt',
            name='bot_status',
        ),
    ]
