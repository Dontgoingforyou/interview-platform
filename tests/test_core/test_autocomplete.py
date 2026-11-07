"""
Тесты для core/autocomplete.py.

Покрывает:
- InternAutocomplete: get_queryset (все/фильтр), get_result_label, get_result_value
- BaseAutocomplete: get_queryset (без модели → AttributeError; с моделью + фильтр),
  get_result_label, get_result_value
- CompanyAutocomplete / DirectionAutocomplete: наследование от BaseAutocomplete
- ManagerAutocomplete: get_queryset (активные/фильтр по имени и email/ошибка БД),
  get_result_label, get_result_value
"""
import pytest
from unittest.mock import MagicMock, patch

from core.autocomplete import (
    InternAutocomplete,
    BaseAutocomplete,
    CompanyAutocomplete,
    DirectionAutocomplete,
    ManagerAutocomplete,
)


def _make_autocomplete(cls, q=''):
    """Создаёт экземпляр автокомплита с нужным запросом."""
    ac = cls()
    ac.q = q
    ac.request = MagicMock()
    return ac


# ---------------------------------------------------------------------------
# InternAutocomplete
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestInternAutocomplete:
    """Тесты для InternAutocomplete."""

    def test_get_queryset_returns_all_when_no_query(self, intern, intern_other):
        """Пустой запрос → все студенты."""
        ac = _make_autocomplete(InternAutocomplete)
        assert ac.get_queryset().count() == 2

    def test_get_queryset_filters_by_full_name(self, intern, intern_other):
        """Поиск 'Иван' → только Иванов."""
        ac = _make_autocomplete(InternAutocomplete, q='Иван')
        qs = ac.get_queryset()
        assert qs.count() == 1
        assert qs.first().full_name == intern.full_name

    def test_get_queryset_ordered_by_full_name(self, intern, intern_other):
        """Результаты упорядочены по full_name."""
        ac = _make_autocomplete(InternAutocomplete)
        names = list(ac.get_queryset().values_list('full_name', flat=True))
        assert names == sorted(names)

    def test_get_result_label_returns_full_name(self, intern):
        """get_result_label возвращает full_name студента."""
        ac = _make_autocomplete(InternAutocomplete)
        assert ac.get_result_label(intern) == intern.full_name

    def test_get_result_value_returns_str_id(self, intern):
        """get_result_value возвращает str(id)."""
        ac = _make_autocomplete(InternAutocomplete)
        assert ac.get_result_value(intern) == str(intern.id)

    def test_get_queryset_empty_when_no_match(self, intern):
        """Поиск без совпадений → пустой queryset."""
        ac = _make_autocomplete(InternAutocomplete, q='ХЗКакойТо')
        assert ac.get_queryset().count() == 0

    def test_get_results_adds_extra_fields(self, intern):
        """get_results добавляет direction_id, telegram_username, email, direction_name."""
        ac = _make_autocomplete(InternAutocomplete)
        context = {'object_list': list(ac.get_queryset())}
        results = ac.get_results(context)
        result = next(
            (r for r in results if str(r.get('id')) == str(intern.id)),
            None,
        )
        assert result is not None
        assert 'direction_id' in result
        assert 'telegram_username' in result
        assert 'email' in result
        assert 'direction_name' in result

    def test_get_results_id_not_in_object_list_gets_empty_fields(self, intern, db):
        """Если id результата нет в object_list, подставляются пустые поля (без запроса в БД)."""
        from unittest.mock import patch
        ac = _make_autocomplete(InternAutocomplete)
        context = {'object_list': []}
        fake_results = [{'id': str(intern.id), 'text': intern.full_name, 'selected_text': intern.full_name}]
        with patch.object(type(ac).__bases__[0], 'get_results', return_value=fake_results):
            results = ac.get_results(context)
        result = next((r for r in results if str(r.get('id')) == str(intern.id)), None)
        assert result is not None
        assert result.get('direction_id') is None
        assert result.get('direction_name') is None
        assert result.get('telegram_username') == ''
        assert result.get('email') == ''


# ---------------------------------------------------------------------------
# BaseAutocomplete (и его наследники CompanyAutocomplete, DirectionAutocomplete)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestBaseAutocomplete:
    """Тесты для BaseAutocomplete."""

    def test_get_queryset_without_model_raises(self):
        """Без model → AttributeError (None.objects.none())."""
        ac = _make_autocomplete(BaseAutocomplete)
        with pytest.raises(AttributeError, match="attribute 'objects'"):
            ac.get_queryset()

    def test_get_result_label_returns_name(self, direction):
        """get_result_label возвращает item.name."""
        ac = _make_autocomplete(DirectionAutocomplete)
        assert ac.get_result_label(direction) == direction.name

    def test_get_result_value_returns_str_id(self, direction):
        """get_result_value возвращает str(id)."""
        ac = _make_autocomplete(DirectionAutocomplete)
        assert ac.get_result_value(direction) == str(direction.id)


@pytest.mark.django_db(databases=['default'])
class TestDirectionAutocomplete:
    """Тесты для DirectionAutocomplete (BaseAutocomplete с model=Direction)."""

    def test_get_queryset_returns_all_directions(self, direction):
        """Без запроса возвращает все направления."""
        ac = _make_autocomplete(DirectionAutocomplete)
        assert ac.get_queryset().filter(id=direction.id).exists()

    def test_get_queryset_filters_by_name(self, direction, db):
        """Поиск по имени фильтрует корректно."""
        from directions.models import Direction
        Direction.objects.create(name='Frontend')
        ac = _make_autocomplete(DirectionAutocomplete, q='Back')
        qs = ac.get_queryset()
        assert all('Back' in obj.name for obj in qs)

    def test_get_queryset_empty_when_no_match(self, direction):
        """Запрос без совпадений → пустой queryset."""
        ac = _make_autocomplete(DirectionAutocomplete, q='НесуществующееНаправление')
        assert ac.get_queryset().count() == 0


@pytest.mark.django_db(databases=['default'])
class TestCompanyAutocomplete:
    """Тесты для CompanyAutocomplete (BaseAutocomplete с model=Company)."""

    def test_get_queryset_returns_all_companies(self, company):
        """Без запроса возвращает все компании."""
        ac = _make_autocomplete(CompanyAutocomplete)
        assert ac.get_queryset().filter(id=company.id).exists()

    def test_get_queryset_filters_by_name(self, company):
        """Поиск по имени компании фильтрует корректно."""
        ac = _make_autocomplete(CompanyAutocomplete, q=company.name[:3])
        assert ac.get_queryset().filter(id=company.id).exists()


# ---------------------------------------------------------------------------
# ManagerAutocomplete
# ---------------------------------------------------------------------------

@pytest.mark.django_db(databases=['default'])
class TestManagerAutocomplete:
    """Тесты для ManagerAutocomplete."""

    def test_get_queryset_returns_only_active_managers(self, manager, manager2, db):
        """get_queryset возвращает только активных менеджеров."""
        from managers.models import Manager
        Manager.objects.filter(email=manager.email).update(is_active=False)
        ac = _make_autocomplete(ManagerAutocomplete)
        emails = list(ac.get_queryset().values_list('email', flat=True))
        assert manager.email not in emails
        assert manager2.email in emails

    def test_get_queryset_filters_by_full_name(self, manager, manager2):
        """Поиск по части full_name менеджера фильтрует корректно."""
        ac = _make_autocomplete(ManagerAutocomplete, q='Алексей')
        qs = ac.get_queryset()
        assert qs.count() == 1
        assert qs.first().email == manager.email

    def test_get_queryset_filters_by_email(self, manager, manager2):
        """Поиск по части email фильтрует корректно."""
        ac = _make_autocomplete(ManagerAutocomplete, q='manager2')
        qs = ac.get_queryset()
        assert any('manager2' in m.email for m in qs)

    def test_get_queryset_ordered_by_full_name(self, manager, manager2):
        """Результаты упорядочены по full_name."""
        ac = _make_autocomplete(ManagerAutocomplete)
        names = list(ac.get_queryset().values_list('full_name', flat=True))
        assert names == sorted(names)

    def test_get_result_label_contains_full_name_and_email(self, manager):
        """get_result_label возвращает строку с full_name и email."""
        ac = _make_autocomplete(ManagerAutocomplete)
        label = ac.get_result_label(manager)
        assert manager.full_name in label
        assert manager.email in label

    def test_get_result_value_returns_email(self, manager):
        """get_result_value возвращает email менеджера (используется как PK в SSO)."""
        ac = _make_autocomplete(ManagerAutocomplete)
        assert ac.get_result_value(manager) == manager.email

    def test_get_queryset_returns_empty_queryset_on_exception(self, db):
        """При исключении в БД возвращается пустой queryset без прокидывания ошибки."""
        from managers.models import Manager
        real_none = Manager.objects.none()
        ac = _make_autocomplete(ManagerAutocomplete)
        with patch('managers.models.Manager.objects') as mock_objs:
            mock_objs.filter.side_effect = Exception('БД недоступна')
            mock_objs.none.return_value = real_none
            qs = ac.get_queryset()
        assert list(qs) == []

    def test_get_result_label_fallback_when_no_full_name(self, manager):
        """get_result_label возвращает str(item), если нет full_name."""
        ac = _make_autocomplete(ManagerAutocomplete)
        item = type('Item', (), {'id': 999, '__str__': lambda self: '999'})()
        assert ac.get_result_label(item) == '999'

    def test_get_result_value_fallback_when_no_email(self, manager):
        """get_result_value возвращает str(item.id), если нет email или не строка."""
        ac = _make_autocomplete(ManagerAutocomplete)
        item = MagicMock()
        item.email = None
        item.id = 42
        assert ac.get_result_value(item) == '42'
