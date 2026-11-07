"""
Тесты для утилит приложения interviews.
"""
import pytest

from interviews.utils import get_or_create_company, map_company_name


@pytest.mark.django_db
@pytest.mark.utils
class TestMapCompanyName:
    """Тесты для функции map_company_name."""

    def test_map_company_name_with_variant(self):
        """Проверка нормализации названия компании с вариантом из COMPANY_OPTIONS."""
        from core.constants import COMPANY_OPTIONS

        if COMPANY_OPTIONS:
            canonical = list(COMPANY_OPTIONS.keys())[0]
            variants = COMPANY_OPTIONS[canonical]
            if variants:
                result = map_company_name(variants[0])
                assert result == canonical

    def test_map_company_name_unknown_returns_none(self):
        """Неизвестная компания возвращает None (не бигтех)."""
        result = map_company_name('Неизвестная_Компания_Которой_Нет')
        assert result is None

    @pytest.mark.parametrize('input_val', ['', None, '   ', 123])
    def test_map_company_name_non_company_inputs_return_none(self, input_val):
        """Пустая строка, None, пробелы и не-строка возвращают None."""
        result = map_company_name(input_val)
        assert result is None

    def test_map_company_name_exact_match_in_db(self, db):
        """Точное совпадение с именем компании в БД возвращает это имя."""
        from companies.models import Company
        Company.objects.create(name='Тестовая Компания БД', is_bigtech=False)
        result = map_company_name('Тестовая Компания БД')
        assert result == 'Тестовая Компания БД'

    def test_map_company_name_case_sensitive_google(self):
        """Проверка чувствительности к регистру на конкретном значении 'Google'."""
        from core.constants import COMPANY_OPTIONS

        canonical_names = set(COMPANY_OPTIONS.keys())
        result_exact = map_company_name('Google')
        result_lower = map_company_name('google')

        if 'Google' in canonical_names:
            assert result_exact == 'Google'
        else:
            assert result_exact is None

        assert result_lower is None or result_lower == 'Google'


@pytest.mark.django_db
@pytest.mark.utils
class TestGetOrCreateCompany:
    """Тесты для функции get_or_create_company."""

    def test_create_new_company_unknown(self):
        """Создаёт компанию с оригинальным названием, если не бигтех."""
        from companies.models import Company

        result = get_or_create_company('Неизвестная Компания')
        assert result is not None
        company = Company.objects.get(id=result)
        assert company.name == 'Неизвестная Компания'
        assert company.is_bigtech is False

    def test_create_bigtech_company(self):
        """Создаёт компанию с is_bigtech=True для бигтеха из COMPANY_OPTIONS."""
        from core.constants import COMPANY_OPTIONS
        from companies.models import Company

        if not COMPANY_OPTIONS:
            pytest.skip('Нет COMPANY_OPTIONS для теста')

        canonical = list(COMPANY_OPTIONS.keys())[0]
        variants = COMPANY_OPTIONS[canonical]
        if not variants:
            pytest.skip('Нет вариантов для теста')

        result = get_or_create_company(variants[0])
        assert result is not None
        company = Company.objects.get(id=result)
        assert company.name == canonical
        assert company.is_bigtech is True

    def test_get_existing_company(self):
        """Возвращает ID существующей компании без дублирования."""
        from companies.models import Company

        result1 = get_or_create_company('Уникальная Тестовая Компания')
        result2 = get_or_create_company('Уникальная Тестовая Компания')
        assert result1 == result2
        assert Company.objects.filter(name='Уникальная Тестовая Компания').count() == 1

    @pytest.mark.parametrize('input_val', ['', None, '   '])
    def test_returns_none_for_empty_or_none_name(self, input_val):
        """Возвращает None для пустого имени, None и строки из пробелов."""
        result = get_or_create_company(input_val)
        assert result is None

    def test_returns_none_for_non_string(self):
        """Возвращает None для не-строки (например, число)."""
        result = get_or_create_company(123)
        assert result is None

    def test_normalization_uses_canonical_name(self):
        """Использует каноническое имя при нормализации."""
        from core.constants import COMPANY_OPTIONS
        from companies.models import Company

        if not COMPANY_OPTIONS:
            pytest.skip('Нет COMPANY_OPTIONS для теста')

        canonical = list(COMPANY_OPTIONS.keys())[0]
        variants = COMPANY_OPTIONS[canonical]
        if len(variants) < 2:
            pytest.skip('Нет достаточного количества вариантов для теста')

        get_or_create_company(variants[0])
        get_or_create_company(variants[1])

        assert Company.objects.filter(name=canonical).count() == 1


@pytest.mark.django_db(databases=['default'])
@pytest.mark.utils
class TestSessionMayAccessInterviewTranscription:
    def test_no_session_returns_false(self, rf):
        from interviews.utils import session_may_access_interview_transcription

        request = rf.get('/')
        assert session_may_access_interview_transcription(request, 1) is False

    def test_admin_allowed(self, rf, interview):
        from interviews.utils import session_may_access_interview_transcription

        request = rf.get('/')
        request.session = {'keycloak_user': {'sub': '1'}, 'manager_role': 'admin'}
        assert session_may_access_interview_transcription(request, interview.pk) is True

    def test_manager_own_interview(self, rf, interview, manager):
        from interviews.utils import session_may_access_interview_transcription
        from core.constants import KEYCLOAK_GROUP_EMPLOYMENT

        interview.manager_email = manager.email
        interview.save(update_fields=['manager_email'])
        request = rf.get('/')
        request.session = {
            'keycloak_user': {'sub': '1'},
            'manager_role': 'manager',
            'manager_groups': [KEYCLOAK_GROUP_EMPLOYMENT],
            'manager_email': manager.email,
        }
        assert session_may_access_interview_transcription(request, interview.pk) is True

    def test_manager_other_denied(self, rf, interview):
        from interviews.utils import session_may_access_interview_transcription
        from core.constants import KEYCLOAK_GROUP_EMPLOYMENT

        request = rf.get('/')
        request.session = {
            'keycloak_user': {'sub': '1'},
            'manager_role': 'manager',
            'manager_groups': [KEYCLOAK_GROUP_EMPLOYMENT],
            'manager_email': 'other@example.com',
        }
        assert session_may_access_interview_transcription(request, interview.pk) is False

    def test_mentor_allowed_any_interview(self, rf, interview):
        from interviews.utils import session_may_access_interview_transcription
        from core.constants import KEYCLOAK_GROUP_MENTORS

        request = rf.get('/')
        request.session = {
            'keycloak_user': True,
            'manager_role': 'mentor',
            'manager_groups': [KEYCLOAK_GROUP_MENTORS],
            'manager_email': 'mentor@example.com',
        }
        assert session_may_access_interview_transcription(request, interview.pk) is True
