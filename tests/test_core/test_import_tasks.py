"""
Тесты для core/import_tasks.py.

Покрывает async_import_from_file:
- Успешный импорт: возвращает dict со status=success и корректными счётчиками
- Отсутствующие обязательные колонки (без mapping): возвращает dict со status=error
- column_mapping + required_columns: колонки переименовываются, валидация проходит
- column_mapping задан, но колонки файла не совпадают с ключами маппинга: status=error
- progress_callback вызывается сервисом: тело callback выполняется без исключений
- Временный файл удаляется после успешного выполнения (finally-блок)
- Временный файл удаляется при исключении в сервисе (finally-блок)
- Исключение в сервисе прокидывается наружу (CELERY_TASK_EAGER_PROPAGATES=True)
- os.remove бросает исключение — оно подавляется, задача завершается успешно

Примечание: мок-сервис инжектируется через sys.modules, а не через patch
importlib.import_module, чтобы не ломать импорты pandas и других библиотек.
"""
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.import_tasks import async_import_from_file

_SERVICE_PATH = 'some.module.MyService'
_MODULE_PATH = 'some.module'
_PARENT_PATH = 'some'


def _make_csv(tmp_path, filename='test.csv', content=b'name,age\nIvan,25\n'):
    """Создаёт CSV-файл во временной директории и возвращает строковый путь."""
    file_path = tmp_path / filename
    file_path.write_bytes(content)
    return str(file_path)


def _make_mock_module(created=3, skipped=1, duplicates=0, errors_log=None):
    """Возвращает мок-модуль с классом MyService, чей run() возвращает заданные счётчики."""
    errors_log = errors_log or []
    instance = MagicMock()
    instance.run.return_value = (created, skipped, duplicates, errors_log)
    service_class = MagicMock(return_value=instance)
    module = MagicMock()
    module.MyService = service_class
    return module


def _make_mock_module_with_progress(created=1, skipped=0, duplicates=0, errors_log=None):
    """Мок-модуль, чей сервис вызывает progress_callback(processed, total) внутри run()."""
    errors_log = errors_log or []
    captured = {}

    class FakeService:
        def __init__(self, df, progress_callback=None):
            captured['callback'] = progress_callback

        def run(self):
            if captured.get('callback'):
                captured['callback'](1, 10)
            return (created, skipped, duplicates, errors_log)

    module = MagicMock()
    module.MyService = FakeService
    return module


@contextmanager
def _inject_module(mock_module):
    """
    Инжектирует мок-модуль в sys.modules под путём _MODULE_PATH на время блока.

    Использует sys.modules вместо patch(importlib.import_module), чтобы не влиять
    на импорты внутри pandas и других библиотек, которые тоже используют importlib.
    """
    sys.modules[_PARENT_PATH] = MagicMock()
    sys.modules[_MODULE_PATH] = mock_module
    try:
        yield
    finally:
        sys.modules.pop(_MODULE_PATH, None)
        sys.modules.pop(_PARENT_PATH, None)


class TestAsyncImportFromFile:
    """Тесты для Celery-задачи async_import_from_file."""

    def test_success_returns_dict(self, tmp_path):
        """Успешный импорт → dict со status=success и всеми счётчиками."""
        file_path = _make_csv(tmp_path)
        with _inject_module(_make_mock_module(created=3, skipped=1, duplicates=0)):
            result = async_import_from_file.apply(args=[file_path, _SERVICE_PATH]).get()

        assert result['status'] == 'success'
        assert result['created'] == 3
        assert result['skipped'] == 1
        assert result['duplicates'] == 0
        assert 'errors' in result
        assert 'errors_list' in result

    def test_missing_required_columns_returns_error(self, tmp_path):
        """CSV без обязательных колонок + required_columns → status=error без вызова сервиса."""
        file_path = _make_csv(tmp_path, content=b'col1,col2\n1,2\n')
        result = async_import_from_file.apply(
            args=[file_path, _SERVICE_PATH],
            kwargs={'required_columns': ['name', 'age']},
        ).get()

        assert result['status'] == 'error'
        assert 'name' in result['message'] or 'age' in result['message']

    def test_with_column_mapping_validation(self, tmp_path):
        """CSV с оригинальными именами + column_mapping → колонки переименованы, статус success."""
        content = 'Имя,Возраст\nИван,25\n'.encode('utf-8')
        file_path = _make_csv(tmp_path, content=content)
        with _inject_module(_make_mock_module(created=1)):
            result = async_import_from_file.apply(
                args=[file_path, _SERVICE_PATH],
                kwargs={
                    'column_mapping': {'Имя': 'name', 'Возраст': 'age'},
                    'required_columns': ['name', 'age'],
                },
            ).get()

        assert result['status'] == 'success'
        assert result['created'] == 1

    def test_temp_file_deleted_on_success(self, tmp_path):
        """После успешного импорта временный файл удалён (finally-блок)."""
        file_path = _make_csv(tmp_path, filename='del_ok.csv')
        with _inject_module(_make_mock_module()):
            async_import_from_file.apply(args=[file_path, _SERVICE_PATH])

        assert not Path(file_path).exists()

    def test_temp_file_deleted_on_exception(self, tmp_path):
        """При исключении в сервисе файл всё равно удалён (finally-блок)."""
        file_path = _make_csv(tmp_path, filename='del_exc.csv')
        module = _make_mock_module()
        module.MyService = MagicMock(return_value=MagicMock(
            run=MagicMock(side_effect=RuntimeError('сервис упал'))
        ))
        with _inject_module(module):
            with pytest.raises(RuntimeError, match='сервис упал'):
                async_import_from_file.apply(args=[file_path, _SERVICE_PATH])

        assert not Path(file_path).exists()

    def test_exception_propagates(self, tmp_path):
        """Исключение в сервисе прокидывается наружу (CELERY_TASK_EAGER_PROPAGATES=True)."""
        file_path = _make_csv(tmp_path, filename='exc_prop.csv')
        module = _make_mock_module()
        module.MyService = MagicMock(return_value=MagicMock(
            run=MagicMock(side_effect=RuntimeError('ошибка импорта'))
        ))
        with _inject_module(module):
            with pytest.raises(RuntimeError, match='ошибка импорта'):
                async_import_from_file.apply(args=[file_path, _SERVICE_PATH])

    def test_with_column_mapping_missing_columns_returns_error(self, tmp_path):
        """CSV с column_mapping, но ключи маппинга отсутствуют в файле → status=error."""
        content = b'wrong_col1,wrong_col2\n1,2\n'
        file_path = _make_csv(tmp_path, content=content)
        result = async_import_from_file.apply(
            args=[file_path, _SERVICE_PATH],
            kwargs={
                'column_mapping': {'Имя': 'name', 'Возраст': 'age'},
                'required_columns': ['name', 'age'],
            },
        ).get()

        assert result['status'] == 'error'
        assert 'Имя' in result['message'] or 'Возраст' in result['message']

    def test_progress_callback_is_invoked(self, tmp_path):
        """Если сервис вызывает progress_callback — тело callback выполняется без исключений."""
        file_path = _make_csv(tmp_path, filename='progress.csv')
        with _inject_module(_make_mock_module_with_progress(created=1)):
            result = async_import_from_file.apply(args=[file_path, _SERVICE_PATH]).get()

        assert result['status'] == 'success'
        assert result['created'] == 1

    def test_remove_error_in_finally_is_suppressed(self, tmp_path):
        """Если os.remove бросает исключение в finally — оно подавляется, задача завершается успешно."""
        file_path = _make_csv(tmp_path, filename='remove_fail.csv')
        with _inject_module(_make_mock_module()):
            with patch('core.import_tasks.os.remove', side_effect=OSError('нет доступа')):
                result = async_import_from_file.apply(args=[file_path, _SERVICE_PATH]).get()

        assert result['status'] == 'success'
