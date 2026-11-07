# Generated manually for interns_portal: progress bar after page refresh

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0020_interview_add_video_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='interview',
            name='upload_task_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                max_length=255,
                null=True,
                verbose_name='ID задачи загрузки видео (Celery)',
            ),
        ),
    ]
