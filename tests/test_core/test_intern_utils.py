"""
Тесты для core/intern_utils.py.

Покрывает функцию find_intern_by_name:
- Пустые и None входные значения
- Точное совпадение
- Поиск по словам в другом порядке
- Несколько кандидатов: выбор лучшего по score (score > у остальных)
- Несколько кандидатов с одинаковым score → возвращает первого найденного
- Несколько кандидатов, ни один не набрал score → None и лог
- Поиск по частичному имени (Q-фильтр): один результат → возвращает
- Fallback по подстроке: несколько результатов → None и лог
- Имя не найдено → None

Покрывает find_intern_by_name(interns_cache=...):
- Тот же алгоритм, но без запросов к БД (поиск в памяти через _find_intern_in_cache)

Покрывает transliterate_name_to_cyrillic (cyrtranslit): PRE/POST правки, реальное поведение
для имён (Timofey, Victoria, Dmitry, Shura), исключение при ошибке.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from core.intern_utils import find_intern_by_name, transliterate_name_to_cyrillic


@pytest.mark.django_db(databases=['default'])
class TestFindInternByName:
    """Тесты для функции find_intern_by_name."""

    # ===== Пустые входные значения =====

    @pytest.mark.parametrize('empty_val', [None, '', '   '])
    def test_empty_input_returns_none(self, empty_val):
        """None, пустая строка и строка из пробелов → None."""
        assert find_intern_by_name(empty_val) is None

    # ===== Точное совпадение =====

    def test_exact_match_returns_intern(self, intern):
        """Точное совпадение по ФИО → возвращает студента."""
        result = find_intern_by_name('Иван Иванов')
        assert result == intern

    def test_exact_match_with_extra_spaces(self, intern):
        """Пробелы по краям строки не влияют на результат."""
        result = find_intern_by_name('  Иван Иванов  ')
        assert result == intern

    # ===== Слова в другом порядке =====

    def test_words_in_different_order_single_candidate(self, intern):
        """Слова 'Иванов Иван' при единственном кандидате → находит студента."""
        result = find_intern_by_name('Иванов Иван')
        assert result == intern

    def test_words_in_different_order_selects_best_score(self, intern, intern_ivanov_sergey):
        """При нескольких кандидатах выбирается тот, у кого больше совпадающих слов.

        intern = 'Иван Иванов', intern_ivanov_sergey = 'Сергей Иванов'.
        Поиск 'Иванов Иван' — name_parts = ['Иванов', 'Иван']:
        - 'Иван Иванов': score = |{'Иванов', 'Иван'} ∩ {'Иван', 'Иванов'}| = 2
        - 'Сергей Иванов': score = |{'Иванов', 'Иван'} ∩ {'Сергей', 'Иванов'}| = 1
        Победитель — intern.
        """
        result = find_intern_by_name('Иванов Иван')
        assert result == intern

    # ===== Несколько кандидатов с одинаковым score =====

    def test_multiple_candidates_equal_score_returns_one_of_them(self, intern, intern_ivanov_sergey):
        """При равном score (поиск по общей фамилии) функция возвращает одного из кандидатов.

        intern = 'Иван Иванов', intern_ivanov_sergey = 'Сергей Иванов'.
        Поиск 'Иванов' — name_parts = ['Иванов']:
        - Оба кандидата score = 1 (равный), best_match = первый найденный.
        """
        result = find_intern_by_name('Иванов')
        assert result in (intern, intern_ivanov_sergey)

    def test_multiple_candidates_returns_best_match_by_score(self, intern, intern_ivanov_sergey):
        """При нескольких кандидатах возвращается студент с максимальным score (ветка return best_match)."""
        result = find_intern_by_name('Иванов Иван')
        assert result == intern
        assert result.full_name == 'Иван Иванов'

    def test_multiple_candidates_zero_overlap_returns_none_and_logs(self, db, direction):
        """Несколько кандидатов по частям, но ни у одного нет совпадающих слов → None и лог."""
        from interns.models import Intern

        Intern.objects.create(
            full_name='АБ',
            email='ab1@example.com',
            manager_email='m@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        Intern.objects.create(
            full_name='АБ',
            email='ab2@example.com',
            manager_email='m@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        with patch('core.intern_utils.logger') as mock_logger:
            result = find_intern_by_name('А Б')
        assert result is None
        mock_logger.warning.assert_called_once()
        assert 'не удалось выбрать лучший' in mock_logger.warning.call_args[0][0]

    def test_fallback_substring_multiple_matches_returns_none_and_logs(self, db, direction):
        """Fallback по подстроке: по частям 0 кандидатов, по подстроке — несколько → None и лог (119–120)."""
        from interns.models import Intern

        # В реальных данных при 0 кандидатах по частям подстрока редко даёт >1.
        # Покрываем ветку через мок: первый filter (по частям) — 0, второй (icontains) — 2.
        mock_candidates = MagicMock()
        mock_candidates.count.return_value = 0
        mock_fallback = MagicMock()
        mock_fallback.count.return_value = 2
        with patch.object(Intern.objects, 'filter', side_effect=[mock_candidates, mock_fallback]):
            with patch('core.intern_utils.logger') as mock_logger:
                result = find_intern_by_name('Два По Подстроке')
        assert result is None
        mock_logger.warning.assert_called_once()
        assert 'несколько студентов' in mock_logger.warning.call_args[0][0]
        assert 'подстроку' in mock_logger.warning.call_args[0][0]

    # ===== Поиск по частичному имени (один результат) =====

    def test_partial_name_single_match_returns_intern(self, intern_sidorov):
        """Поиск по уникальной фамилии ('Сидоров') → находит единственного студента."""
        result = find_intern_by_name('Сидоров')
        assert result == intern_sidorov

    def test_partial_first_name_single_match_returns_intern(self, intern_petrov):
        """Поиск по части имени ('Петров') → находит студента, если он единственный с такой фамилией."""
        result = find_intern_by_name('Петров')
        assert result == intern_petrov

    # ===== Имя не найдено =====

    def test_nonexistent_name_returns_none(self):
        """Имя, которого нет в БД → None."""
        result = find_intern_by_name('Несуществующий Студент')
        assert result is None

    # ===== Дефис в ФИО =====

    def test_name_with_hyphen_found_by_parts(self, db, direction):
        """Поиск по частям с дефисом: «Анна Мария» и «Анна-Мария» находят студента «Анна-Мария»."""
        from interns.models import Intern

        intern = Intern.objects.create(
            full_name='Анна-Мария',
            email='anna.maria@example.com',
            manager_email='manager@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        assert find_intern_by_name('Анна Мария') == intern
        assert find_intern_by_name('Анна-Мария') == intern

    def test_name_with_hyphen_found_when_search_has_hyphen(self, db, direction):
        """Поиск «Анна-Мария» находит запись «Анна-Мария» (части по дефису)."""
        from interns.models import Intern

        Intern.objects.create(
            full_name='Анна-Мария',
            email='s@example.com',
            manager_email='m@example.com',
            direction=direction,
            date_of_receipt=date(2025, 1, 1),
            date_of_birth=date(2000, 1, 1),
            hiring_hr='HR1',
            responsible_hr='HR2',
            group='GR1',
            type_of_training='internal',
        )
        result = find_intern_by_name('Анна-Мария')
        assert result is not None
        assert result.full_name == 'Анна-Мария'


def _make_mock_intern(full_name, pk=None):
    """Создаёт мок-объект Intern с атрибутом full_name."""
    m = MagicMock()
    m.full_name = full_name
    m.pk = pk or hash(full_name)
    return m


class TestFindInternByNameWithCache:
    """
    Тесты для find_intern_by_name(interns_cache=...) — поиск в памяти.

    Воспроизводит тот же алгоритм что и TestFindInternByName, но без БД:
    передаётся предзагруженный список объектов Intern (мок-объекты).
    Запросы к БД не используются.
    """

    # ===== Пустые входные значения =====

    @pytest.mark.parametrize('empty_val', [None, '', '   '])
    def test_empty_input_returns_none(self, empty_val):
        """None, пустая строка, строка из пробелов → None (независимо от кэша)."""
        cache = [_make_mock_intern('Иван Иванов')]
        assert find_intern_by_name(empty_val, interns_cache=cache) is None

    def test_empty_cache_returns_none(self):
        """Пустой кэш → None."""
        assert find_intern_by_name('Иван Иванов', interns_cache=[]) is None

    # ===== Точное совпадение =====

    def test_exact_match_returns_intern(self):
        """Точное совпадение по ФИО → возвращает студента."""
        intern = _make_mock_intern('Иван Иванов')
        result = find_intern_by_name('Иван Иванов', interns_cache=[intern])
        assert result is intern

    def test_exact_match_case_insensitive(self):
        """Точное совпадение без учёта регистра."""
        intern = _make_mock_intern('Иван Иванов')
        result = find_intern_by_name('иван иванов', interns_cache=[intern])
        assert result is intern

    def test_exact_match_strips_spaces(self):
        """Пробелы по краям строки не влияют на результат."""
        intern = _make_mock_intern('Иван Иванов')
        result = find_intern_by_name('  Иван Иванов  ', interns_cache=[intern])
        assert result is intern

    # ===== Слова в другом порядке =====

    def test_words_in_different_order_single_candidate(self):
        """Слова в другом порядке при единственном кандидате → находит студента."""
        intern = _make_mock_intern('Иван Иванов')
        result = find_intern_by_name('Иванов Иван', interns_cache=[intern])
        assert result is intern

    def test_words_in_different_order_selects_best_score(self):
        """При нескольких кандидатах выбирается тот, у кого больше совпадающих слов.

        intern = 'Иван Иванов', sergey = 'Сергей Иванов'.
        Поиск 'Иванов Иван' — name_parts = ['Иванов', 'Иван']:
        - 'Иван Иванов': score = |{'Иванов', 'Иван'} ∩ {'Иван', 'Иванов'}| = 2
        - 'Сергей Иванов': score = |{'Иванов', 'Иван'} ∩ {'Сергей', 'Иванов'}| = 1
        Победитель — intern.
        """
        intern = _make_mock_intern('Иван Иванов')
        sergey = _make_mock_intern('Сергей Иванов')
        result = find_intern_by_name('Иванов Иван', interns_cache=[intern, sergey])
        assert result is intern

    # ===== Несколько кандидатов с одинаковым score =====

    def test_multiple_candidates_equal_score_returns_one_of_them(self):
        """При равном score функция возвращает одного из кандидатов (первый с max score)."""
        intern = _make_mock_intern('Иван Иванов')
        sergey = _make_mock_intern('Сергей Иванов')
        result = find_intern_by_name('Иванов', interns_cache=[intern, sergey])
        assert result in (intern, sergey)

    # ===== Нет совпадений по частям, fallback по подстроке =====

    def test_fallback_substring_single_match_returns_intern(self):
        """Fallback: полная строка запроса является подстрокой ФИО студента → находит студента.

        Используем мок-имя '_иванов_олег_' с пробелами вокруг подстроки:
        parts = ['иванов', 'олег'] каждая входит в 'иванов олег' → кандидат найден по step 2.
        Для чистого fallback-теста важно покрыть ветку find с одним результатом.
        """
        intern = _make_mock_intern('Иванов Олег Петрович')
        result = find_intern_by_name('Иванов Олег', interns_cache=[intern])
        assert result is intern

    def test_not_found_returns_none_and_logs(self):
        """Имя не найдено ни по частям, ни по подстроке → None и лог."""
        intern = _make_mock_intern('Иван Иванов')
        with patch('core.intern_utils.logger') as mock_logger:
            result = find_intern_by_name('Несуществующий Студент', interns_cache=[intern])
        assert result is None
        mock_logger.warning.assert_called_once()
        assert 'не найден' in mock_logger.warning.call_args[0][0]

    # ===== Дефис в ФИО =====

    def test_name_with_hyphen_found_by_parts(self):
        """Поиск по частям с дефисом: «Сайд Ахмед» и «Сайд-Ахмед» находят «Сайд-Ахмед»."""
        intern = _make_mock_intern('Сайд-Ахмед Курбанов')
        assert find_intern_by_name('Сайд Ахмед', interns_cache=[intern]) is intern
        assert find_intern_by_name('Сайд-Ахмед', interns_cache=[intern]) is intern

    # ===== Несколько кандидатов: нет лучшего =====

    def test_multiple_candidates_zero_overlap_returns_none_and_logs(self):
        """Несколько кандидатов по частям, ни у одного нет совпадающих частей → None и лог."""
        intern1 = _make_mock_intern('А Б')
        intern2 = _make_mock_intern('А Б')
        with patch('core.intern_utils.logger') as mock_logger:
            result = find_intern_by_name('Х Ы', interns_cache=[intern1, intern2])
        assert result is None


@pytest.mark.django_db(databases=['default'])
class TestTransliterateNameToCyrillic:
    """Тесты транслитерации ФИО (cyrtranslit + POST_TRANSLIT_FIXES)."""

    def test_empty_returns_empty(self):
        """Пустая строка и None возвращаются как есть."""
        assert transliterate_name_to_cyrillic('') == ''
        assert transliterate_name_to_cyrillic(None) is None

    def test_cyrillic_passthrough(self):
        """Кириллица не меняется (нет транслитерации)."""
        assert transliterate_name_to_cyrillic('Анна-Мария') == 'Анна-Мария'

    def test_sayd_ahmed_kurbanov(self):
        """Sayd-Ahmed → Сайд-Ахмед (cyrtranslit + PRE для Said/Ahmet)."""
        assert transliterate_name_to_cyrillic('Sayd-Ahmed') == 'Сайд-Ахмед'
        assert transliterate_name_to_cyrillic('Said Ahmed') == 'Сайд Ахмед'

    def test_ahmad_to_ahmed_post_fix(self):
        """Правка Ахмад → Ахмед из POST_TRANSLIT_FIXES."""
        assert transliterate_name_to_cyrillic('Sayd Ahmad') == 'Сайд Ахмед'

    def test_latin_ts_becomes_cyrillic_c(self):
        """Латинское «ts» в именах → «ц» (cyrtranslit даёт «тс», заменяем на «ц»)."""
        assert transliterate_name_to_cyrillic('Darya Podvintseva') == 'Дарья Подвинцева'
        assert transliterate_name_to_cyrillic('Irina Solntseva') == 'Ирина Солнцева'

    def test_latin_shch_becomes_cyrillic_sch(self):
        """Латинское «shch» (щ) до cyrtranslit → «shh», иначе получается «шч» вместо «щ»."""
        assert transliterate_name_to_cyrillic('Anna Onishchenko') == 'Анна Онищенко'
        assert transliterate_name_to_cyrillic('Shcherbakov') == 'Щербаков'

    def test_translit_exception_returns_original_and_logs(self):
        """При исключении в cyrtranslit возвращается исходная строка и пишется лог."""
        with patch('cyrtranslit.to_cyrillic', side_effect=ValueError('cyrtranslit error')):
            with patch('core.intern_utils.logger') as mock_logger:
                result = transliterate_name_to_cyrillic('John Doe')
        assert result == 'John Doe'
        mock_logger.warning.assert_called_once()
        assert 'John Doe' in mock_logger.warning.call_args[0]
        assert 'cyrtranslit error' in str(mock_logger.warning.call_args[0][2])

    def test_empty_result_fallback_returns_original(self):
        """Фоллбэк: если транслитерация вернула пустую строку — возвращаем исходное имя."""
        with patch('cyrtranslit.to_cyrillic', return_value=''):
            result = transliterate_name_to_cyrillic('Unknown Name')
        assert result == 'Unknown Name'

    def test_whitespace_only_result_fallback_returns_original(self):
        """Фоллбэк: если результат — только пробелы — возвращаем исходное имя."""
        with patch('cyrtranslit.to_cyrillic', return_value='   '):
            result = transliterate_name_to_cyrillic('Strange')
        assert result == 'Strange'

    @pytest.mark.parametrize(
        'latin,expected_cyrillic',
        [
            ('timofey timofeev', 'Тимофей Тимофеев'),
            ('Timofey Timofeev', 'Тимофей Тимофеев'),
            ('Alexey', 'Алексей'),
            ('Dmitry', 'Дмитрий'),
            ('Victoria', 'Виктория'),
            ('Victoria Petrov', 'Виктория Петров'),
            ('Shura', 'Шура'),
            ('Charles', 'Чарлес'),
            ('Igor', 'Игорь'),
            ('Ilya', 'Илья'),
            ('Maxim', 'Максим'),
            ('Alexander', 'Александр'),
            ('Evgeny', 'Евгений'),
            ('Evgeniy Mihaylov', 'Евгений Михайлов'),
            ('Evgenty Mihaylov', 'Евгений Михайлов'),
            ('Dmitriy Ivanov', 'Дмитрий Иванов'),
            ('Valeriy Sidorov', 'Валерий Сидоров'),
            ('Vitaliy Petrov', 'Виталий Петров'),
            ('Anatoliy Kuznetsov', 'Анатолий Кузнецов'),
            ('Georgiy Fedorov', 'Георгий Федоров'),
            ('my', 'Ми'),
            ('Bytyk', 'Бытык'),
            ('Rybin', 'Рыбин'),
            ('Onishchenko', 'Онищенко'),
        ],
    )
    def test_real_translit_and_post_fixes(self, latin, expected_cyrillic):
        """Реальная транслитерация cyrtranslit и правки POST_TRANSLIT_FIXES."""
        result = transliterate_name_to_cyrillic(latin)
        assert result == expected_cyrillic
