from django.db import models
from django.db.models import Q

from core.constants import (
    INTERN_STATUS_LEFT,
    INTERN_STATUS_OFFER,
    SAD_INTERN_STATUS_ON_PROJECT,
)


class SadInternQuerySet(models.QuerySet):
    """Custom QuerySet для SadIntern с методами фильтрации."""

    def exclude_left_interns(self):
        """
        Исключает записи, у которых у интерна ручной статус «Оффер» или «Ушёл».

        Пустой manual_status у интерна считается активным и не отфильтровывается.
        """
        return self.exclude(
            Q(intern__manual_status=INTERN_STATUS_LEFT) | Q(intern__manual_status=INTERN_STATUS_OFFER)
        )

    def for_main_waiting_list(self):
        """
        Основной список «Грустят» и метрики как на сайте: без on_project, без интернов оффер/ушёл.

        Порог даты выхода на собесы и менеджер здесь не проверяются (grandfathering существующих записей).
        """
        return self.exclude(status=SAD_INTERN_STATUS_ON_PROJECT).exclude_left_interns()


class SadInternManager(models.Manager):
    """Custom Manager для SadIntern."""

    def get_queryset(self):
        return SadInternQuerySet(self.model, using=self._db)

    def exclude_left_interns(self):
        """Proxy метод для вызова exclude_left_interns из QuerySet."""
        return self.get_queryset().exclude_left_interns()

    def for_main_waiting_list(self):
        """Proxy для for_main_waiting_list."""
        return self.get_queryset().for_main_waiting_list()
