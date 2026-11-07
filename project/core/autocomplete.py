import logging
from typing import ClassVar, Optional, Type
from dal import autocomplete
from django.db.models import Q, Model

from core.intern_utils import transliterate_name_to_cyrillic, transliterate_query_to_latin
from interns.models import Intern
from directions.models import Direction
from companies.models import Company

logger = logging.getLogger(__name__)


class InternAutocomplete(autocomplete.Select2QuerySetView):
    """ Автокомплит для студентов по full_name. """
    paginate_by = 50

    def get_queryset(self):
        """ Метод возвращает набор записей из БД для поиска. """
        qs = Intern.objects.select_related('direction').order_by('full_name')

        if self.q:
            qs = qs.filter(full_name__icontains=self.q)

        return qs

    def get_result_label(self, item):
        """ Метод определяет какое значение будет отображаться в выпадающем списке. """
        return item.full_name

    def get_result_value(self, item):
        """ Метод определяет какое значение будет отправлено в форме при выборе. """
        return str(item.id)

    def get_results(self, context):
        """
        Переопределяем метод для добавления дополнительных данных к каждому результату.
        Это позволит автоматически подгружать направление, telegram и email при выборе студента.
        Используем object_list из context, чтобы избежать N+1 запросов.
        """
        results = super().get_results(context)
        object_list = list(context.get('object_list') or [])
        intern_by_id = {str(intern.id): intern for intern in object_list}

        for result in results:
            intern_id = result.get('id')
            if intern_id:
                intern = intern_by_id.get(str(intern_id))
                if intern:
                    result['direction_id'] = intern.direction_id
                    result['telegram_username'] = intern.telegram_username or ''
                    result['email'] = intern.email or ''
                    result['direction_name'] = intern.direction.name if intern.direction else None
                else:
                    result['direction_id'] = None
                    result['direction_name'] = None
                    result['telegram_username'] = ''
                    result['email'] = ''

        return results


class BaseAutocomplete(autocomplete.Select2QuerySetView):
    """ Базовый класс для автокомплитов. """

    paginate_by = 50
    model: ClassVar[Optional[Type[Model]]] = None

    def get_queryset(self):
        """ Метод возвращает набор записей из БД для поиска. """
        if not self.model:
            return self.model.objects.none()

        qs = self.model.objects.all().order_by('name')
        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs

    def get_result_label(self, item):
        """ Метод определяет какое значение будет отображаться в выпадающем списке автокомплита. """
        return item.name

    def get_result_value(self, item):
        """ Метод определяет какое значение будет отправлено в форме при выборе элемента. """
        return str(item.id)


class CompanyAutocomplete(BaseAutocomplete):
    """ Автокомплит для компаний. """
    model = Company


class DirectionAutocomplete(BaseAutocomplete):
    """ Автокомплит для направлений. """
    model = Direction


class ManagerAutocomplete(autocomplete.Select2QuerySetView):
    """
    Автокомплит для менеджеров из локальной БД (SSO/Keycloak).

    Работает с таблицей managers, которая автоматически заполняется
    при логине пользователей через SSO.
    """
    paginate_by = 50

    def get_queryset(self):
        """
        Возвращает список активных менеджеров из локальной БД.
        Поддерживает поиск по имени (в т.ч. на кириллице) и email.
        """
        try:
            from managers.models import Manager
            qs = Manager.objects.filter(is_active=True).order_by('full_name')

            if self.q:
                # full_name в БД может хранится на латинице (SSO/Keycloak) или кириллице.
                # Ищем по исходному запросу и по его транслитерации кириллица→латиница.
                latin_q = transliterate_query_to_latin(self.q)
                name_filter = Q(full_name__icontains=self.q)
                if latin_q:
                    name_filter |= Q(full_name__icontains=latin_q)
                qs = qs.filter(name_filter | Q(email__icontains=self.q))

            return qs

        except Exception as e:
            logger.error(f"Ошибка при работе с БД менеджеров: {e}", exc_info=True)
            from managers.models import Manager
            return Manager.objects.none()

    def get_result_label(self, item):
        """Отображение в выпадающем списке (имя — для отображения, латиница → кириллица)."""
        if hasattr(item, 'full_name'):
            raw = item.full_name or ''
            display_name = transliterate_name_to_cyrillic(raw) or raw
            return f"{display_name} ({item.email})"
        return str(item)

    def get_result_value(self, item):
        """Значение для отправки в форме (email как PK)"""
        if hasattr(item, 'email') and isinstance(item.email, str):
            return item.email
        return str(item.id)
