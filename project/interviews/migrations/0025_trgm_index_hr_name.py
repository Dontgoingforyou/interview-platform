from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """
    Создаёт GIN-индекс по триграммам на поле hr_name модели Interview.
    Ускоряет поиск LIKE '%query%' (icontains) по имени HR в базе собеседований.
    TrigramExtension — idempotent, безопасно вызывать повторно.
    """

    dependencies = [
        ('interviews', '0024_performance_indexes'),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name='interview',
            index=GinIndex(
                fields=['hr_name'],
                name='interviews_hr_name_trgm_idx',
                opclasses=['gin_trgm_ops'],
            ),
        ),
    ]
