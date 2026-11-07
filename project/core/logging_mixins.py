import logging
from typing import Dict, Optional


def get_user_label_for_log(request) -> str:
    """Метка пользователя для логов без email."""
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        full_name = getattr(user, 'full_name', None)
        if isinstance(full_name, str) and full_name:
            return full_name
        username = getattr(user, 'username', None)
        if isinstance(username, str) and username:
            return username
        user_id = getattr(user, 'id', None)
        if user_id is not None:
            return f'user_id={user_id}'
        return 'authenticated'
    session = getattr(request, 'session', None)
    if session is not None and hasattr(session, 'get'):
        manager_name = session.get('manager_name')
        if isinstance(manager_name, str) and manager_name:
            return manager_name
    return 'anonymous'


class LoggingMixin:
    """
    Базовый миксин для логирования операций с моделями.

    Атрибуты:
        logger_name: Имя логгера (по умолчанию берется из модели)
        log_level: Уровень логирования (по умолчанию INFO)
        log_fields: Список полей модели для логирования (по умолчанию все)
    """
    logger_name: Optional[str] = None
    log_level: int = logging.INFO
    log_fields: Optional[list] = None  # None = все поля

    def get_logger(self) -> logging.Logger:
        """Возвращает logger для текущего view."""
        if self.logger_name:
            return logging.getLogger(self.logger_name)

        # Автоматическое определение имени логгера из модели
        if hasattr(self, 'model') and self.model:
            app_label = self.model._meta.app_label
            model_name = self.model._meta.model_name
            return logging.getLogger(f'{app_label}.{model_name}')

        return logging.getLogger(__name__)

    def get_user_info(self, request) -> str:
        """Возвращает информацию о пользователе для логирования."""
        label = get_user_label_for_log(request)
        if label == 'anonymous':
            return 'Анонимный пользователь'
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False) and getattr(user, 'id', None) is not None:
            return f'{label} (ID: {user.id})'
        return label

    def get_object_repr(self, obj) -> str:
        """Возвращает строковое представление объекта."""
        if hasattr(obj, 'pk'):
            model_name = obj._meta.verbose_name if hasattr(obj, '_meta') else type(obj).__name__
            return f"{model_name} (ID: {obj.pk})"
        return str(obj)

    def get_field_changes(self, form) -> Dict[str, tuple]:
        """
        Возвращает словарь изменённых полей с их старыми и новыми значениями.

        Returns:
            Dict[field_name, (old_value, new_value)]
        """
        if not hasattr(form, 'changed_data') or not hasattr(form, 'initial'):
            return {}

        changes = {}
        for field_name in form.changed_data:
            # Пропускаем поля, не указанные в log_fields (если он задан)
            if self.log_fields and field_name not in self.log_fields:
                continue

            old_value = form.initial.get(field_name, None)
            new_value = form.cleaned_data.get(field_name, None)

            # Скрываем чувствительные данные
            if 'password' in field_name.lower():
                old_value = '***'
                new_value = '***'

            changes[field_name] = (old_value, new_value)

        return changes

    def format_changes(self, changes: Dict[str, tuple]) -> str:
        """Форматирует изменения для вывода в лог."""
        if not changes:
            return "Нет изменений"

        formatted = []
        for field, (old, new) in changes.items():
            formatted.append(f"{field}: '{old}' → '{new}'")

        return "; ".join(formatted)


class CreateLoggingMixin(LoggingMixin):
    """
    Миксин для логирования создания объектов.
    Использование:
        class MyCreateView(CreateLoggingMixin, CreateView):
            model = MyModel
            ...
    """

    def form_valid(self, form):
        """Переопределяем для логирования создания объекта."""
        response = super().form_valid(form)

        logger = self.get_logger()
        user_info = self.get_user_info(self.request)
        obj_repr = self.get_object_repr(self.object)

        # Собираем данные созданного объекта
        created_data = {}
        for field in form.cleaned_data:
            if self.log_fields is None or field in self.log_fields:
                value = form.cleaned_data[field]
                if 'password' not in field.lower():
                    created_data[field] = value

        logger.log(
            self.log_level,
            f"[СОЗДАНИЕ] Пользователь {user_info} создал {obj_repr}. "
            f"Данные: {created_data}"
        )

        return response


class UpdateLoggingMixin(LoggingMixin):
    """
    Миксин для логирования обновления объектов.
    Использование:
        class MyUpdateView(UpdateLoggingMixin, UpdateView):
            model = MyModel
            ...
    """

    def form_valid(self, form):
        """Переопределяем для логирования обновления объекта."""
        # Получаем изменения ДО сохранения
        changes = self.get_field_changes(form)
        obj_repr = self.get_object_repr(self.object)

        response = super().form_valid(form)

        logger = self.get_logger()
        user_info = self.get_user_info(self.request)

        if changes:
            formatted_changes = self.format_changes(changes)
            logger.log(
                self.log_level,
                f"[ОБНОВЛЕНИЕ] Пользователь {user_info} обновил {obj_repr}. "
                f"Изменения: {formatted_changes}"
            )
        else:
            logger.log(
                self.log_level,
                f"[ОБНОВЛЕНИЕ] Пользователь {user_info} сохранил {obj_repr} "
                f"без изменений."
            )

        return response


class DeleteLoggingMixin(LoggingMixin):
    """
    Миксин для логирования удаления объектов.

    Использование:
        class MyDeleteView(DeleteLoggingMixin, DeleteView):
            model = MyModel
            ...
    """

    def delete(self, request, *args, **kwargs):
        """Переопределяем для логирования удаления объекта."""
        # Сохраняем информацию об объекте ДО удаления
        obj = self.get_object()
        obj_repr = self.get_object_repr(obj)

        # Собираем важные данные удаляемого объекта
        obj_data = {}
        if self.log_fields:
            for field in self.log_fields:
                if hasattr(obj, field):
                    obj_data[field] = getattr(obj, field)
        else:
            # Логируем все поля (кроме служебных)
            for field in obj._meta.fields:
                if not field.name.startswith('_'):
                    obj_data[field.name] = getattr(obj, field.name, None)

        response = super().delete(request, *args, **kwargs)

        logger = self.get_logger()
        user_info = self.get_user_info(request)

        logger.log(
            self.log_level,
            f"[УДАЛЕНИЕ] Пользователь {user_info} удалил {obj_repr}. "
            f"Данные удалённого объекта: {obj_data}"
        )

        return response


class BulkDeleteLoggingMixin(LoggingMixin):
    """
    Миксин для логирования массового удаления объектов.
    Использование в API views или admin actions.
    """
    def log_bulk_delete(self, request, queryset, count: int):
        """Логирует массовое удаление объектов."""
        logger = self.get_logger()
        user_info = self.get_user_info(request)

        model_name = queryset.model._meta.verbose_name_plural

        # Собираем ID удаляемых объектов
        deleted_ids = list(queryset.values_list('pk', flat=True))

        logger.log(
            self.log_level,
            f"[МАССОВОЕ УДАЛЕНИЕ] Пользователь {user_info} удалил {count} "
            f"{model_name}. ID удалённых объектов: {deleted_ids}"
        )


class ImportLoggingMixin(LoggingMixin):
    """
    Миксин для логирования операций импорта.
    Использование:
        class MyImportView(ImportLoggingMixin, View):
            ...
    """

    def log_import_start(self, request, filename: str, row_count: int):
        """Логирует начало импорта."""
        logger = self.get_logger()
        user_info = self.get_user_info(request)

        logger.info(
            f"[ИМПОРТ - НАЧАЛО] Пользователь {user_info} начал импорт из файла "
            f"'{filename}' ({row_count} строк)"
        )

    def log_import_success(self, request, created: int, updated: int, errors: int):
        """Логирует успешное завершение импорта."""
        logger = self.get_logger()
        user_info = self.get_user_info(request)

        logger.info(
            f"[ИМПОРТ - УСПЕХ] Пользователь {user_info} завершил импорт. "
            f"Создано: {created}, Обновлено: {updated}, Ошибок: {errors}"
        )

    def log_import_error(self, request, error: Exception, filename: str = None):
        """Логирует ошибку импорта."""
        logger = self.get_logger()
        user_info = self.get_user_info(request)

        filename_str = f" из файла '{filename}'" if filename else ""
        logger.error(
            f"[ИМПОРТ - ОШИБКА] Пользователь {user_info} получил ошибку "
            f"при импорте{filename_str}: {str(error)}",
            exc_info=True
        )


class ExportLoggingMixin(LoggingMixin):
    """
    Миксин для логирования операций экспорта.
    """

    def log_export(self, request, format_type: str, count: int):
        """Логирует экспорт данных."""
        logger = self.get_logger()
        user_info = self.get_user_info(request)

        model_name = self.model._meta.verbose_name_plural if hasattr(self, 'model') else 'данных'

        logger.info(
            f"[ЭКСПОРТ] Пользователь {user_info} экспортировал {count} "
            f"{model_name} в формате {format_type}"
        )


# Комбинированный миксин для стандартных CRUD операций
class CRUDLoggingMixin(CreateLoggingMixin, UpdateLoggingMixin, DeleteLoggingMixin):
    """
    Комбинированный миксин, включающий логирование всех CRUD операций.
    Использование:
        class MyModelViewSet(CRUDLoggingMixin, ModelViewSet):
            model = MyModel
            ...
    """
    pass


def log_signal(signal_name: str = None, logger_name: str = None):
    """
    Декоратор для логирования Django сигналов.
    Использование:
        @log_signal('post_save', 'myapp.signals')
        def my_signal_handler(sender, instance, created, **kwargs):
            # логика обработчика
            pass

    Параметры:
        signal_name: Название сигнала (например, 'post_save', 'pre_delete')
        logger_name: Имя логгера (по умолчанию берется из sender)
    """
    def decorator(func):
        def wrapper(sender, instance=None, **kwargs):
            # Определяем логгер
            if logger_name:
                logger = logging.getLogger(logger_name)
            elif sender:
                app_label = sender._meta.app_label if hasattr(sender, '_meta') else 'unknown'
                model_name = sender._meta.model_name if hasattr(sender, '_meta') else 'unknown'
                logger = logging.getLogger(f'{app_label}.{model_name}')
            else:
                logger = logging.getLogger(__name__)

            # Формируем информацию об объекте
            obj_info = ''
            if instance:
                if hasattr(instance, 'pk'):
                    model_name = instance._meta.verbose_name if hasattr(instance, '_meta') else type(instance).__name__
                    obj_info = f"{model_name} (ID: {instance.pk})"
                else:
                    obj_info = str(instance)

            # Определяем тип операции из kwargs
            operation = signal_name or 'signal'
            if 'created' in kwargs:
                operation = 'создание' if kwargs['created'] else 'обновление'

            # Логируем начало
            logger.info(
                f"[СИГНАЛ: {operation.upper()}] Обработка {obj_info}"
            )

            try:
                # Вызываем оригинальную функцию
                result = func(sender, instance=instance, **kwargs)

                # Логируем успех
                logger.info(
                    f"[СИГНАЛ: {operation.upper()}] Успешно обработан {obj_info}"
                )

                return result
            except Exception as e:
                # Логируем ошибку
                logger.error(
                    f"[СИГНАЛ: {operation.upper()}] Ошибка при обработке {obj_info}: {str(e)}",
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


class ApiCRUDLoggingMixin:
    """
    Миксин для логирования CRUD-операций в DRF ViewSets.

    Автоматически логирует create, update/partial_update, destroy:
    - ID созданного/изменённого/удалённого объекта
    - Список изменённых полей (для update)
    - Метка пользователя (без email), выполнившего операцию

    Использование:
        class MyViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
            api_logger_name = 'myapp.mymodel'   # имя логгера из settings.LOGGING
    """

    api_logger_name: Optional[str] = None

    def _get_api_logger(self) -> logging.Logger:
        if self.api_logger_name:
            return logging.getLogger(self.api_logger_name)
        return logging.getLogger(self.__class__.__module__)

    def _get_api_user_label(self, request) -> str:
        return get_user_label_for_log(request)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            obj_id = response.data.get('id') if response.data else '?'
            self._get_api_logger().info(
                'API [СОЗДАНИЕ] id=%s — %s', obj_id, self._get_api_user_label(request)
            )
        return response

    def update(self, request, *args, **kwargs):
        pk = kwargs.get('pk') or self.kwargs.get('pk')
        response = super().update(request, *args, **kwargs)
        if response.status_code == 200:
            fields = list(request.data.keys())
            self._get_api_logger().info(
                'API [ОБНОВЛЕНИЕ] id=%s поля=%s — %s', pk, fields, self._get_api_user_label(request)
            )
        return response

    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get('pk') or self.kwargs.get('pk')
        response = super().destroy(request, *args, **kwargs)
        if response.status_code == 204:
            self._get_api_logger().info(
                'API [УДАЛЕНИЕ] id=%s — %s', pk, self._get_api_user_label(request)
            )
        return response
