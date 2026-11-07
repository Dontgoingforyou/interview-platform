"""
Синхронизация студентов из CSV/XLSX (merge-only, без затирания заполненных полей).
"""
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError

from core.constants import INTERN_IMPORT_COLUMN_MAPPING
from core.file_utils import read_file_content, rename_columns, validate_required_columns
from interns.services import InternSyncImportService


class Command(BaseCommand):
    help = 'Синхронизирует студентов из файла: дополняет пустые поля, не затирает существующие.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            required=True,
            help='Путь к CSV или XLSX из файла',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только отчёт без записи в БД',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']

        if not os.path.isfile(file_path):
            raise CommandError(f'Файл не найден: {file_path}')

        with open(file_path, 'rb') as f:
            uploaded = SimpleUploadedFile(os.path.basename(file_path), f.read())
            df = read_file_content(uploaded)

        is_valid, missing_headers = validate_required_columns(
            df, ['full_name'], INTERN_IMPORT_COLUMN_MAPPING,
        )
        if not is_valid:
            raise CommandError(
                f"В файле отсутствуют обязательные столбцы: {', '.join(missing_headers)}"
            )
        df = rename_columns(df, INTERN_IMPORT_COLUMN_MAPPING)

        service = InternSyncImportService(df, dry_run=dry_run)
        created_or_updated, skipped, unchanged, errors = service.run()

        mode = 'DRY-RUN' if dry_run else 'SYNC'
        self.stdout.write(
            self.style.SUCCESS(
                f'[{mode}] Строк в файле: {len(df)}. '
                f'Создано/обновлено: {created_or_updated}, '
                f'без изменений: {unchanged}, ошибок: {skipped}.'
            )
        )
        if errors:
            self.stdout.write(self.style.WARNING('Ошибки (первые 20):'))
            for err in errors[:20]:
                self.stdout.write(f'  - {err}')
