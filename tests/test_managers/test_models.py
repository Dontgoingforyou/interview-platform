"""
Тесты модели Manager.

Покрывают:
- Создание записи и поля по умолчанию
- Свойства: is_admin, is_employment_manager, is_cv_manager, is_education_manager
- Строковое представление __str__
- email как первичный ключ
- Сортировка по full_name

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.models    - для группировки тестов
"""
import pytest
from django.db import IntegrityError

from managers.models import Manager


@pytest.mark.django_db(databases=['default'])
@pytest.mark.models
class TestManagerModel:
    """Тесты модели Manager."""

    # --- Создание и поля по умолчанию ---

    def test_manager_creation_with_all_fields(self):
        """Менеджер создаётся с корректными данными."""
        manager = Manager.objects.create(
            email='test@example.com',
            full_name='Тест Тестов',
            username='test_user',
            groups=['employment-managers'],
            is_active=True,
        )
        assert manager.email == 'test@example.com'
        assert manager.full_name == 'Тест Тестов'
        assert manager.username == 'test_user'
        assert manager.groups == ['employment-managers']
        assert manager.is_active is True

    def test_email_is_primary_key(self):
        """email используется как первичный ключ."""
        manager = Manager.objects.create(
            email='pk@example.com',
            full_name='PK Менеджер',
            username='pk_manager',
            groups=[],
        )
        assert manager.pk == 'pk@example.com'

    def test_is_active_default_true(self):
        """По умолчанию менеджер активен."""
        manager = Manager.objects.create(
            email='default@example.com',
            full_name='Default Менеджер',
            username='default_manager',
            groups=[],
        )
        assert manager.is_active is True

    def test_groups_default_empty_list(self):
        """По умолчанию groups — пустой список."""
        manager = Manager.objects.create(
            email='nogroups@example.com',
            full_name='NoGroups Менеджер',
            username='no_groups',
        )
        assert manager.groups == []

    def test_created_at_auto_set(self):
        """created_at устанавливается автоматически при создании."""
        manager = Manager.objects.create(
            email='created@example.com',
            full_name='Created Test',
            username='created',
            groups=[],
        )
        assert manager.created_at is not None

    def test_updated_at_auto_set(self):
        """updated_at устанавливается автоматически."""
        manager = Manager.objects.create(
            email='updated@example.com',
            full_name='Updated Test',
            username='updated',
            groups=[],
        )
        assert manager.updated_at is not None

    # --- __str__ ---

    def test_str_representation(self, manager):
        """Строковое представление — имя и email в скобках."""
        expected = f'{manager.full_name} ({manager.email})'
        assert str(manager) == expected

    # --- Флаги ролей ---

    @pytest.mark.parametrize('groups, prop, expected', [
        (['role_admin'],   'is_admin',              True),
        (['employment-managers'], 'is_admin',              False),
        ([],                      'is_admin',              False),
        (['employment-managers'], 'is_employment_manager', True),
        (['cv-managers'],         'is_employment_manager', False),
        (['cv-managers'],         'is_cv_manager',         True),
        (['employment-managers'], 'is_cv_manager',         False),
        (['education'],           'is_education_manager',  True),
        (['employment-managers'], 'is_education_manager',  False),
    ])
    def test_role_flag(self, groups, prop, expected):
        """Флаг роли зависит от наличия соответствующей группы."""
        m = Manager.objects.create(
            email=f'role-{prop}-{str(expected).lower()}@test.com',
            full_name='Тестовый Менеджер',
            username=f'role_{prop}_{str(expected).lower()}',
            groups=groups,
        )
        assert getattr(m, prop) is expected

    # --- Несколько групп ---

    def test_manager_can_have_multiple_groups(self):
        """Менеджер может принадлежать нескольким группам одновременно."""
        manager = Manager.objects.create(
            email='multi@test.com',
            full_name='Multi Groups',
            username='multi',
            groups=['role_admin', 'employment-managers', 'cv-managers'],
        )
        assert manager.is_admin is True
        assert manager.is_employment_manager is True
        assert manager.is_cv_manager is True
        assert manager.is_education_manager is False

    def test_admin_manager_fixture_has_correct_roles(self, admin_manager):
        """Фикстура admin_manager имеет корректные роли."""
        assert admin_manager.is_admin is True
        assert admin_manager.is_employment_manager is True

    # --- Уникальность и ограничения ---

    def test_email_unique_constraint(self):
        """email должен быть уникальным — дублирование вызывает ошибку."""
        Manager.objects.create(
            email='unique@test.com',
            full_name='Первый',
            username='first',
            groups=[],
        )
        with pytest.raises((IntegrityError, Exception)):
            Manager.objects.create(
                email='unique@test.com',
                full_name='Второй',
                username='second',
                groups=[],
            )

    # --- Сортировка ---

    def test_manager_ordering_by_full_name(self):
        """Менеджеры сортируются по полю full_name в алфавитном порядке."""
        Manager.objects.create(
            email='z@test.com', full_name='Яблоков', username='z', groups=[],
        )
        Manager.objects.create(
            email='a@test.com', full_name='Абрамов', username='a', groups=[],
        )
        managers = list(Manager.objects.filter(email__in=['z@test.com', 'a@test.com']))
        assert managers[0].full_name == 'Абрамов'
        assert managers[1].full_name == 'Яблоков'

    # --- Обновление ---

    def test_manager_update_saves_correctly(self, manager):
        """Обновление данных менеджера сохраняется в БД."""
        manager.full_name = 'Обновлённое Имя'
        manager.save()
        manager.refresh_from_db()
        assert manager.full_name == 'Обновлённое Имя'

    def test_manager_deactivation(self, manager):
        """Деактивация менеджера сохраняется корректно."""
        manager.is_active = False
        manager.save()
        manager.refresh_from_db()
        assert manager.is_active is False

    # --- Фильтрация ---

    def test_filter_by_is_active(self, manager, manager2):
        """Фильтрация активных менеджеров работает корректно."""
        manager2.is_active = False
        manager2.save()
        active = Manager.objects.filter(is_active=True)
        inactive = Manager.objects.filter(is_active=False)
        assert manager in active
        assert manager2 in inactive
        assert manager2 not in active

    def test_filter_by_email_works(self, manager, admin_manager):
        """Фильтрация по email (PK) работает корректно."""
        found = Manager.objects.get(email=manager.email)
        assert found == manager
        assert found.email == manager.email
