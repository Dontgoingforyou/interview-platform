"""
Тесты для core/logging_mixins.py.

Покрывает:
- LoggingMixin: get_user_info, get_object_repr, get_field_changes, format_changes
- CreateLoggingMixin: form_valid (логирование, маскировка пароля)
- UpdateLoggingMixin: form_valid (с изменениями, без изменений)
- DeleteLoggingMixin: delete (логирование перед удалением)
- BulkDeleteLoggingMixin: log_bulk_delete
- ImportLoggingMixin: log_import_start, log_import_success, log_import_error
- ExportLoggingMixin: log_export
- log_signal: вызов обработчика, операция по created-kwarg, прокидывание исключения
- ApiCRUDLoggingMixin: create/update/destroy с логированием
"""
import logging
import pytest
from django.http import HttpResponse
from unittest.mock import MagicMock

from core.logging_mixins import (
    LoggingMixin,
    CreateLoggingMixin,
    UpdateLoggingMixin,
    DeleteLoggingMixin,
    BulkDeleteLoggingMixin,
    ImportLoggingMixin,
    ExportLoggingMixin,
    log_signal,
    ApiCRUDLoggingMixin,
)


class TestGetUserInfo:
    """Тесты для LoggingMixin.get_user_info."""

    def setup_method(self):
        self.mixin = LoggingMixin()

    def _make_request(self, *, authenticated=False, username='user1', user_id=42,
                      manager_email=None, manager_name=None):
        """Создаёт мок request с нужными атрибутами."""
        request = MagicMock()
        user = MagicMock()
        user.is_authenticated = authenticated
        user.username = username
        user.id = user_id
        request.user = user

        session = {}
        if manager_email:
            session['manager_email'] = manager_email
        if manager_name:
            session['manager_name'] = manager_name
        request.session = session

        return request

    def test_authenticated_user_returns_username_and_id(self):
        """Аутентифицированный request.user → 'username (ID: id)'."""
        request = self._make_request(authenticated=True, username='vasya', user_id=7)
        result = self.mixin.get_user_info(request)
        assert result == 'vasya (ID: 7)'

    def test_session_manager_returns_name_without_email(self):
        """Сессия с manager_name → только имя (без email в логах)."""
        request = self._make_request(
            authenticated=False,
            manager_email='boss@example.com',
            manager_name='Иван Иванов',
        )
        result = self.mixin.get_user_info(request)
        assert result == 'Иван Иванов'

    def test_session_without_manager_name_is_anonymous(self):
        """Сессия только с manager_email без manager_name → анонимный пользователь."""
        request = self._make_request(
            authenticated=False,
            manager_email='anon@example.com',
        )
        result = self.mixin.get_user_info(request)
        assert result == 'Анонимный пользователь'

    def test_anonymous_user_returns_default_string(self):
        """Нет ни user, ни сессии → 'Анонимный пользователь'."""
        request = self._make_request(authenticated=False)
        result = self.mixin.get_user_info(request)
        assert result == 'Анонимный пользователь'


class TestGetObjectRepr:
    """Тесты для LoggingMixin.get_object_repr."""

    def setup_method(self):
        self.mixin = LoggingMixin()

    def test_object_with_pk_returns_verbose_name_and_id(self):
        """Объект с pk и _meta.verbose_name → 'verbose_name (ID: pk)'."""
        obj = MagicMock()
        obj.pk = 99
        obj._meta.verbose_name = 'студент'
        result = self.mixin.get_object_repr(obj)
        assert result == 'студент (ID: 99)'

    def test_object_without_pk_returns_str(self):
        """Объект без pk → str(obj)."""
        class SimpleObj:
            def __str__(self):
                return 'SimpleObject'

        result = self.mixin.get_object_repr(SimpleObj())
        assert result == 'SimpleObject'


class TestGetFieldChanges:
    """Тесты для LoggingMixin.get_field_changes."""

    def setup_method(self):
        self.mixin = LoggingMixin()

    def _make_form(self, changed_data, initial, cleaned_data):
        """Создаёт мок-форму с нужными атрибутами."""
        form = MagicMock()
        form.changed_data = changed_data
        form.initial = initial
        form.cleaned_data = cleaned_data
        return form

    def test_no_changes_returns_empty_dict(self):
        """Нет изменённых полей → {}."""
        form = self._make_form(changed_data=[], initial={}, cleaned_data={})
        assert self.mixin.get_field_changes(form) == {}

    def test_changed_field_returns_old_and_new(self):
        """Изменённое поле → {'field': (old, new)}."""
        form = self._make_form(
            changed_data=['name'],
            initial={'name': 'Старое'},
            cleaned_data={'name': 'Новое'},
        )
        result = self.mixin.get_field_changes(form)
        assert result == {'name': ('Старое', 'Новое')}

    def test_password_field_is_masked(self):
        """Поле, содержащее 'password', маскируется значением '***'."""
        form = self._make_form(
            changed_data=['password_hash'],
            initial={'password_hash': 'secret123'},
            cleaned_data={'password_hash': 'newsecret'},
        )
        result = self.mixin.get_field_changes(form)
        assert result == {'password_hash': ('***', '***')}

    def test_log_fields_filters_out_unlisted_fields(self):
        """Если log_fields задан, в результат попадают только перечисленные поля."""
        self.mixin.log_fields = ['name']
        form = self._make_form(
            changed_data=['name', 'email'],
            initial={'name': 'Старое', 'email': 'old@example.com'},
            cleaned_data={'name': 'Новое', 'email': 'new@example.com'},
        )
        result = self.mixin.get_field_changes(form)
        assert 'email' not in result
        assert result == {'name': ('Старое', 'Новое')}
        self.mixin.log_fields = None  # сбрасываем

    def test_form_without_changed_data_returns_empty(self):
        """Форма без атрибутов changed_data/initial → {}."""
        form = object()
        assert self.mixin.get_field_changes(form) == {}

    def test_field_missing_from_initial_uses_none(self):
        """Поле, которого нет в initial, получает old_value=None."""
        form = self._make_form(
            changed_data=['new_field'],
            initial={},
            cleaned_data={'new_field': 'значение'},
        )
        result = self.mixin.get_field_changes(form)
        assert result == {'new_field': (None, 'значение')}

    def test_multiple_changed_fields(self):
        """Несколько изменённых полей → все попадают в результат."""
        form = self._make_form(
            changed_data=['a', 'b'],
            initial={'a': 1, 'b': 2},
            cleaned_data={'a': 10, 'b': 20},
        )
        result = self.mixin.get_field_changes(form)
        assert result == {'a': (1, 10), 'b': (2, 20)}


class TestFormatChanges:
    """Тесты для LoggingMixin.format_changes."""

    def setup_method(self):
        self.mixin = LoggingMixin()

    def test_empty_dict_returns_no_changes(self):
        """Пустой словарь → 'Нет изменений'."""
        assert self.mixin.format_changes({}) == 'Нет изменений'

    def test_single_field_format(self):
        """Одно поле → 'field: 'old' → 'new''."""
        result = self.mixin.format_changes({'name': ('Старое', 'Новое')})
        assert result == "name: 'Старое' → 'Новое'"

    def test_multiple_fields_joined_by_semicolon(self):
        """Несколько полей → объединены через '; '."""
        changes = {'a': (1, 2), 'b': (3, 4)}
        result = self.mixin.format_changes(changes)
        parts = result.split('; ')
        assert len(parts) == 2
        assert "a: '1' → '2'" in parts
        assert "b: '3' → '4'" in parts


# ---------------------------------------------------------------------------
# Вспомогательные базовые классы для тестирования миксинов, которым нужен
# super().form_valid / super().delete
# ---------------------------------------------------------------------------

class _BaseCreateSuper:
    """Минимальный 'super' для CreateLoggingMixin."""
    def form_valid(self, form):
        obj = MagicMock()
        obj.pk = 1
        obj._meta = MagicMock()
        obj._meta.verbose_name = 'объект'
        self.object = obj
        return HttpResponse('OK')


class _BaseUpdateSuper:
    """Минимальный 'super' для UpdateLoggingMixin."""
    def form_valid(self, form):
        return HttpResponse('OK')


class _BaseDeleteSuper:
    """Минимальный 'super' для DeleteLoggingMixin."""
    def get_object(self):
        obj = MagicMock()
        obj.pk = 5
        obj._meta = MagicMock()
        obj._meta.verbose_name = 'студент'
        obj._meta.fields = []
        return obj

    def delete(self, request, *args, **kwargs):
        return HttpResponse('Deleted', status=200)


def _anon_request():
    """Создаёт анонимный запрос (без SSO, без user)."""
    request = MagicMock()
    request.user = MagicMock()
    request.user.is_authenticated = False
    request.session = {}
    return request


# ---------------------------------------------------------------------------
# CreateLoggingMixin
# ---------------------------------------------------------------------------

class TestCreateLoggingMixin:
    """Тесты для CreateLoggingMixin.form_valid."""

    def _make_view(self):
        class _View(CreateLoggingMixin, _BaseCreateSuper):
            logger_name = 'test.create'

        view = _View()
        view.request = _anon_request()
        return view

    def test_form_valid_returns_response(self):
        """form_valid возвращает HttpResponse от super()."""
        view = self._make_view()
        form = MagicMock()
        form.cleaned_data = {'name': 'Тест'}
        response = view.form_valid(form)
        assert response.status_code == 200

    def test_form_valid_logs_creation(self, caplog):
        """form_valid логирует [СОЗДАНИЕ] с данными объекта."""
        view = self._make_view()
        form = MagicMock()
        form.cleaned_data = {'name': 'Иван'}
        with caplog.at_level(logging.INFO, logger='test.create'):
            view.form_valid(form)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[СОЗДАНИЕ]' in logged
        assert 'Иван' in logged

    def test_form_valid_excludes_password_from_log(self, caplog):
        """Поле с 'password' в названии не попадает в лог."""
        view = self._make_view()
        form = MagicMock()
        form.cleaned_data = {'name': 'Иван', 'password': 'secret123'}
        with caplog.at_level(logging.INFO, logger='test.create'):
            view.form_valid(form)
        logged = ' '.join(r.message for r in caplog.records)
        assert 'secret123' not in logged


# ---------------------------------------------------------------------------
# UpdateLoggingMixin
# ---------------------------------------------------------------------------

class TestUpdateLoggingMixin:
    """Тесты для UpdateLoggingMixin.form_valid."""

    def _make_view(self):
        class _View(UpdateLoggingMixin, _BaseUpdateSuper):
            logger_name = 'test.update'

        view = _View()
        view.request = _anon_request()
        obj = MagicMock()
        obj.pk = 3
        obj._meta = MagicMock()
        obj._meta.verbose_name = 'студент'
        view.object = obj
        return view

    def test_form_valid_returns_response(self):
        """form_valid возвращает HttpResponse от super()."""
        view = self._make_view()
        form = MagicMock()
        form.changed_data = []
        form.initial = {}
        form.cleaned_data = {}
        assert view.form_valid(form).status_code == 200

    def test_form_valid_logs_with_changes(self, caplog):
        """При изменениях логирует [ОБНОВЛЕНИЕ] с новым и старым значениями."""
        view = self._make_view()
        form = MagicMock()
        form.changed_data = ['name']
        form.initial = {'name': 'Старое'}
        form.cleaned_data = {'name': 'Новое'}
        with caplog.at_level(logging.INFO, logger='test.update'):
            view.form_valid(form)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ОБНОВЛЕНИЕ]' in logged
        assert 'Старое' in logged
        assert 'Новое' in logged

    def test_form_valid_logs_without_changes(self, caplog):
        """Без изменений логирует [ОБНОВЛЕНИЕ] и 'без изменений'."""
        view = self._make_view()
        form = MagicMock()
        form.changed_data = []
        form.initial = {}
        form.cleaned_data = {}
        with caplog.at_level(logging.INFO, logger='test.update'):
            view.form_valid(form)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ОБНОВЛЕНИЕ]' in logged
        assert 'без изменений' in logged


# ---------------------------------------------------------------------------
# DeleteLoggingMixin
# ---------------------------------------------------------------------------

class TestDeleteLoggingMixin:
    """Тесты для DeleteLoggingMixin.delete."""

    def _make_view(self):
        class _View(DeleteLoggingMixin, _BaseDeleteSuper):
            logger_name = 'test.delete'

        return _View()

    def test_delete_returns_response(self):
        """delete возвращает HttpResponse от super()."""
        view = self._make_view()
        response = view.delete(_anon_request())
        assert response.status_code == 200

    def test_delete_logs_deletion(self, caplog):
        """delete логирует [УДАЛЕНИЕ] с информацией об объекте."""
        view = self._make_view()
        with caplog.at_level(logging.INFO, logger='test.delete'):
            view.delete(_anon_request())
        logged = ' '.join(r.message for r in caplog.records)
        assert '[УДАЛЕНИЕ]' in logged

    def test_delete_logs_specific_fields_when_log_fields_set(self, caplog):
        """Если log_fields задан, в лог попадают только перечисленные поля объекта."""
        class _ViewWithFields(DeleteLoggingMixin, _BaseDeleteSuper):
            logger_name = 'test.delete'
            log_fields = ['name']

            def get_object(self):
                obj = MagicMock()
                obj.pk = 7
                obj._meta = MagicMock()
                obj._meta.verbose_name = 'объект'
                obj.name = 'Тестовое имя'
                return obj

        view = _ViewWithFields()
        with caplog.at_level(logging.INFO, logger='test.delete'):
            view.delete(_anon_request())
        logged = ' '.join(r.message for r in caplog.records)
        assert '[УДАЛЕНИЕ]' in logged
        assert 'Тестовое имя' in logged


# ---------------------------------------------------------------------------
# BulkDeleteLoggingMixin
# ---------------------------------------------------------------------------

class TestBulkDeleteLoggingMixin:
    """Тесты для BulkDeleteLoggingMixin.log_bulk_delete."""

    def _make_mixin(self):
        class _Mixin(BulkDeleteLoggingMixin):
            logger_name = 'test.bulk'

        return _Mixin()

    def test_log_bulk_delete_logs_count_and_ids(self, caplog):
        """log_bulk_delete логирует [МАССОВОЕ УДАЛЕНИЕ], количество и ID."""
        mixin = self._make_mixin()
        queryset = MagicMock()
        queryset.model._meta.verbose_name_plural = 'студенты'
        queryset.values_list.return_value = [1, 2, 3]
        with caplog.at_level(logging.INFO, logger='test.bulk'):
            mixin.log_bulk_delete(_anon_request(), queryset, count=3)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[МАССОВОЕ УДАЛЕНИЕ]' in logged
        assert '3' in logged
        assert '[1, 2, 3]' in logged


# ---------------------------------------------------------------------------
# ImportLoggingMixin
# ---------------------------------------------------------------------------

class TestImportLoggingMixin:
    """Тесты для ImportLoggingMixin."""

    def _make_mixin(self):
        class _Mixin(ImportLoggingMixin):
            logger_name = 'test.import'

        return _Mixin()

    def test_log_import_start_logs_filename_and_row_count(self, caplog):
        """log_import_start логирует [ИМПОРТ - НАЧАЛО] с именем файла и кол-вом строк."""
        mixin = self._make_mixin()
        with caplog.at_level(logging.INFO, logger='test.import'):
            mixin.log_import_start(_anon_request(), 'data.csv', 100)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ИМПОРТ - НАЧАЛО]' in logged
        assert 'data.csv' in logged
        assert '100' in logged

    def test_log_import_success_logs_counters(self, caplog):
        """log_import_success логирует [ИМПОРТ - УСПЕХ] со счётчиками."""
        mixin = self._make_mixin()
        with caplog.at_level(logging.INFO, logger='test.import'):
            mixin.log_import_success(_anon_request(), created=10, updated=5, errors=2)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ИМПОРТ - УСПЕХ]' in logged
        assert '10' in logged
        assert '5' in logged
        assert '2' in logged

    def test_log_import_error_with_filename(self, caplog):
        """log_import_error с filename логирует [ИМПОРТ - ОШИБКА] с именем файла."""
        mixin = self._make_mixin()
        with caplog.at_level(logging.ERROR, logger='test.import'):
            mixin.log_import_error(_anon_request(), ValueError('Ошибка!'), filename='file.csv')
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ИМПОРТ - ОШИБКА]' in logged
        assert 'file.csv' in logged
        assert 'Ошибка!' in logged

    def test_log_import_error_without_filename(self, caplog):
        """log_import_error без filename работает корректно."""
        mixin = self._make_mixin()
        with caplog.at_level(logging.ERROR, logger='test.import'):
            mixin.log_import_error(_anon_request(), RuntimeError('Упс'))
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ИМПОРТ - ОШИБКА]' in logged
        assert 'Упс' in logged


# ---------------------------------------------------------------------------
# ExportLoggingMixin
# ---------------------------------------------------------------------------

class TestExportLoggingMixin:
    """Тесты для ExportLoggingMixin.log_export."""

    def _make_mixin(self):
        class _Mixin(ExportLoggingMixin):
            logger_name = 'test.export'
            model = MagicMock()
            model._meta.verbose_name_plural = 'студенты'

        return _Mixin()

    def test_log_export_logs_format_and_count(self, caplog):
        """log_export логирует [ЭКСПОРТ] с форматом и количеством."""
        mixin = self._make_mixin()
        with caplog.at_level(logging.INFO, logger='test.export'):
            mixin.log_export(_anon_request(), format_type='CSV', count=50)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ЭКСПОРТ]' in logged
        assert 'CSV' in logged
        assert '50' in logged

    def test_log_export_without_model_uses_default_name(self, caplog):
        """Без атрибута model используется 'данных' как имя."""
        class _MixinNoModel(ExportLoggingMixin):
            logger_name = 'test.export'

        mixin = _MixinNoModel()
        with caplog.at_level(logging.INFO, logger='test.export'):
            mixin.log_export(_anon_request(), format_type='XLSX', count=5)
        logged = ' '.join(r.message for r in caplog.records)
        assert '[ЭКСПОРТ]' in logged
        assert 'данных' in logged


# ---------------------------------------------------------------------------
# log_signal
# ---------------------------------------------------------------------------

class TestLogSignalDecorator:
    """Тесты для декоратора log_signal."""

    def test_decorated_handler_is_called_and_returns_result(self):
        """Декорированный обработчик вызывается и возвращает результат."""
        @log_signal('post_save', 'test.signal')
        def my_handler(sender, instance=None, **kwargs):
            return 'result'

        sender = MagicMock()
        sender._meta.app_label = 'myapp'
        sender._meta.model_name = 'mymodel'
        instance = MagicMock()
        instance.pk = 1
        instance._meta.verbose_name = 'объект'

        result = my_handler(sender, instance=instance)
        assert result == 'result'

    @pytest.mark.parametrize('created, expected_op', [
        (True, 'создание'),
        (False, 'обновление'),
    ])
    def test_created_kwarg_determines_operation_in_log(self, caplog, created, expected_op):
        """created=True → 'создание', created=False → 'обновление' в логе."""
        @log_signal(logger_name='test.signal')
        def handler(sender, instance=None, **kwargs):
            pass

        sender = MagicMock()
        sender._meta.app_label = 'app'
        sender._meta.model_name = 'model'

        with caplog.at_level(logging.INFO, logger='test.signal'):
            handler(sender, instance=MagicMock(), created=created)

        logged = ' '.join(r.message for r in caplog.records).lower()
        assert expected_op in logged

    def test_exception_in_handler_is_reraised(self):
        """Исключение в обработчике прокидывается наружу."""
        @log_signal('post_delete', 'test.signal')
        def bad_handler(sender, instance=None, **kwargs):
            raise ValueError('Ошибка обработки')

        sender = MagicMock()
        sender._meta.app_label = 'myapp'
        sender._meta.model_name = 'mymodel'

        with pytest.raises(ValueError, match='Ошибка обработки'):
            bad_handler(sender, instance=MagicMock())

    def test_exception_is_logged_before_reraise(self, caplog):
        """Исключение логируется как ERROR перед прокидыванием."""
        @log_signal(logger_name='test.signal')
        def bad_handler(sender, instance=None, **kwargs):
            raise RuntimeError('Критический сбой')

        sender = MagicMock()
        sender._meta.app_label = 'a'
        sender._meta.model_name = 'b'

        with caplog.at_level(logging.ERROR, logger='test.signal'):
            with pytest.raises(RuntimeError, match='Критический сбой'):
                bad_handler(sender, instance=MagicMock())

        assert any(r.levelno == logging.ERROR for r in caplog.records)

    def test_signal_name_used_when_no_created_kwarg(self, caplog):
        """Без created kwarg используется signal_name из декоратора."""
        @log_signal('my_custom_signal', 'test.signal')
        def handler(sender, instance=None, **kwargs):
            pass

        sender = MagicMock()
        sender._meta.app_label = 'app'
        sender._meta.model_name = 'model'

        with caplog.at_level(logging.INFO, logger='test.signal'):
            handler(sender, instance=MagicMock())

        logged = ' '.join(r.message for r in caplog.records).upper()
        assert 'MY_CUSTOM_SIGNAL' in logged


# ---------------------------------------------------------------------------
# ApiCRUDLoggingMixin
# ---------------------------------------------------------------------------

class _BaseApiViewSet:
    """Минимальная имитация DRF ViewSet для тестирования ApiCRUDLoggingMixin."""
    kwargs = {}

    def create(self, request, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 201
        resp.data = {'id': 42}
        return resp

    def update(self, request, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 200
        return resp

    def destroy(self, request, *args, **kwargs):
        resp = MagicMock()
        resp.status_code = 204
        return resp


class _LoggedViewSet(ApiCRUDLoggingMixin, _BaseApiViewSet):
    api_logger_name = 'test.api'


def _api_request(email='user@example.com', data=None):
    """Создаёт мок API-запроса с аутентифицированным пользователем."""
    request = MagicMock()
    user = MagicMock()
    user.is_authenticated = True
    user.email = email
    user.username = email
    request.user = user
    request.data = data or {}
    return request


class TestApiCRUDLoggingMixin:
    """Тесты для ApiCRUDLoggingMixin."""

    def test_create_logs_id_on_201(self, caplog):
        """create при статусе 201 → лог API [СОЗДАНИЕ] с id созданного объекта."""
        vs = _LoggedViewSet()
        with caplog.at_level(logging.INFO, logger='test.api'):
            vs.create(_api_request())
        logged = ' '.join(r.message for r in caplog.records)
        assert 'СОЗДАНИЕ' in logged
        assert '42' in logged

    def test_create_no_log_on_non_201(self, caplog):
        """create при статусе != 201 → лог НЕ пишется."""
        class _FailBase(_BaseApiViewSet):
            def create(self, request, *args, **kwargs):
                resp = MagicMock()
                resp.status_code = 400
                resp.data = {}
                return resp

        class _FailSet(ApiCRUDLoggingMixin, _FailBase):
            api_logger_name = 'test.api'

        vs = _FailSet()
        with caplog.at_level(logging.INFO, logger='test.api'):
            vs.create(_api_request())
        assert not caplog.records

    def test_update_logs_pk_and_fields_on_200(self, caplog):
        """update при статусе 200 → лог API [ОБНОВЛЕНИЕ] с pk и полями."""
        vs = _LoggedViewSet()
        request = _api_request(data={'name': 'Новое', 'email': 'x@x.com'})
        with caplog.at_level(logging.INFO, logger='test.api'):
            vs.update(request, pk=7)
        logged = ' '.join(r.message for r in caplog.records)
        assert 'ОБНОВЛЕНИЕ' in logged
        assert '7' in logged

    def test_destroy_logs_pk_on_204(self, caplog):
        """destroy при статусе 204 → лог API [УДАЛЕНИЕ] с pk."""
        vs = _LoggedViewSet()
        with caplog.at_level(logging.INFO, logger='test.api'):
            vs.destroy(_api_request(), pk=99)
        logged = ' '.join(r.message for r in caplog.records)
        assert 'УДАЛЕНИЕ' in logged
        assert '99' in logged

    def test_destroy_no_log_on_non_204(self, caplog):
        """destroy при статусе != 204 → лог НЕ пишется."""
        class _NoDeleteBase(_BaseApiViewSet):
            def destroy(self, request, *args, **kwargs):
                resp = MagicMock()
                resp.status_code = 403
                return resp

        class _NoDeleteSet(ApiCRUDLoggingMixin, _NoDeleteBase):
            api_logger_name = 'test.api'

        vs = _NoDeleteSet()
        with caplog.at_level(logging.INFO, logger='test.api'):
            vs.destroy(_api_request(), pk=1)
        assert not caplog.records

    def test_get_api_user_label_returns_anonymous_for_unauthenticated(self):
        """_get_api_user_label для неаутентифицированного → 'anonymous'."""
        vs = _LoggedViewSet()
        request = MagicMock()
        request.user = None
        request.session = {}
        assert vs._get_api_user_label(request) == 'anonymous'
