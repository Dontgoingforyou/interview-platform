from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    """
    Создаёт GIN-индекс по триграммам на поле full_name модели Intern.
    Ускоряет поиск LIKE '%query%' (icontains) при автодополнении стажёров.
    Требует расширения pg_trgm (PostgreSQL).
    """

    dependencies = [
        ('interns', '0019_performance_indexes'),
    ]

    operations = [
        TrigramExtension(),
        migrations.AddIndex(
            model_name='intern',
            index=GinIndex(
                fields=['full_name'],
                name='interns_full_name_trgm_idx',
                opclasses=['gin_trgm_ops'],
            ),
        ),
    ]
