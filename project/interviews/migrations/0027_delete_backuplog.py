from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0026_interview_add_interview_format'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BackupLog',
        ),
    ]
