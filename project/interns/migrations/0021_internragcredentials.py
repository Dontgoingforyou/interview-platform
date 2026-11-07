# Generated migration for InternRAGCredentials.
# Таблицу создаёт пользователь (makemigrations не запускался по запросу).

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interns', '0020_trgm_index_full_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternRAGCredentials',
            fields=[
                ('intern', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    primary_key=True,
                    related_name='rag_credentials',
                    serialize=False,
                    to='interns.intern',
                    verbose_name='Студент',
                )),
                ('phone_tg_hh', models.CharField(
                    blank=True,
                    max_length=20,
                    null=True,
                    verbose_name='Телефон для TG/HH',
                )),
                ('password_hh', models.CharField(
                    blank=True,
                    max_length=500,
                    null=True,
                    verbose_name='Пароль для HH',
                )),
                ('password_tg', models.CharField(
                    blank=True,
                    max_length=500,
                    null=True,
                    verbose_name='Пароль для TG',
                )),
                ('corporate_tg_username', models.CharField(
                    blank=True,
                    help_text='Через @, например @username',
                    max_length=100,
                    null=True,
                    verbose_name='Ник корпоративного TG',
                )),
                ('work_email', models.EmailField(
                    blank=True,
                    max_length=254,
                    null=True,
                    verbose_name='Рабочая почта',
                )),
                ('telethon_session_string', models.TextField(
                    blank=True,
                    help_text='Заполняется задачей после успешной авторизации в TG.',
                    null=True,
                    verbose_name='Строка сессии Telethon',
                )),
                ('session_generated_at', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Дата генерации сессии',
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    verbose_name='Дата создания',
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    verbose_name='Дата обновления',
                )),
            ],
            options={
                'verbose_name': 'Учётные данные RAG стажёра',
                'verbose_name_plural': 'Учётные данные RAG стажёров',
                'db_table': 'interns_rag_credentials',
            },
        ),
    ]
