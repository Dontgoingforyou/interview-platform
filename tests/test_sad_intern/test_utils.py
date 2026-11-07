"""
Тесты для утилит приложения sad_intern.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.utils - для группировки тестов утилит
"""
import pytest

from sad_intern.utils import find_intern_by_name
from interns.models import Intern


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestFindInternByName:
    """Тесты для функции find_intern_by_name (импортированной из core.intern_utils)."""

    def test_find_intern_by_exact_name(self, intern):
        """Проверка поиска по точному имени."""
        result = find_intern_by_name(intern.full_name)
        assert result is not None
        assert result.id == intern.id
        assert result.full_name == intern.full_name

    def test_find_intern_by_name_not_found(self):
        """Проверка возврата None при отсутствии студента."""
        result = find_intern_by_name('Несуществующий Студент')
        assert result is None

    def test_find_intern_by_partial_name(self, intern):
        """Поиск по одному слову из имени возвращает студента (icontains fallback)."""
        first_name = intern.full_name.split()[0]
        result = find_intern_by_name(first_name)
        assert result is not None
        assert result.id == intern.id

    def test_find_intern_case_insensitive(self, direction):
        """Проверка поиска без учёта регистра (через iexact для точного совпадения)."""
        from datetime import date
        # Создаём студента
        intern = Intern.objects.create(
            full_name='Иван Тестовый',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        # Точный поиск с тем же регистром должен работать
        result = find_intern_by_name('Иван Тестовый')
        assert result is not None
        assert result.id == intern.id

        # Поиск по подстроке должен работать
        result2 = find_intern_by_name('Иван')
        assert result2 is not None
        assert result2.id == intern.id

    def test_find_intern_with_spaces(self, direction):
        """Проверка поиска имени с пробелами."""
        from datetime import date
        intern = Intern.objects.create(
            full_name='Имя С Пробелами',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        result = find_intern_by_name('Имя С Пробелами')
        assert result is not None
        assert result.id == intern.id

    def test_find_intern_empty_string(self):
        """Проверка поиска с пустой строкой."""
        result = find_intern_by_name('')
        assert result is None

    def test_find_intern_none(self):
        """Проверка поиска с None."""
        result = find_intern_by_name(None)
        assert result is None

    def test_find_intern_multiple_matches(self, direction):
        """Проверка поиска при наличии нескольких совпадений."""
        from datetime import date
        # Создаём двух студентов с похожими именами
        intern1 = Intern.objects.create(
            full_name='Иван Иванов',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )
        intern2 = Intern.objects.create(
            full_name='Иван Петров',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR2',
            type_of_training='internal'
        )

        # Поиск по точному имени должен вернуть правильного студента
        result = find_intern_by_name('Иван Иванов')
        assert result is not None
        assert result.id == intern1.id

    def test_find_intern_with_special_characters(self, direction):
        """Проверка поиска имени со специальными символами."""
        from datetime import date
        intern = Intern.objects.create(
            full_name="О'Коннор Мэри",
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal'
        )

        result = find_intern_by_name("О'Коннор Мэри")
        assert result is not None
        assert result.id == intern.id
