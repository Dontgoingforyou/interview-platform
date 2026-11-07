from django.db import models
from core.constants import KEYCLOAK_GROUP_ADMIN, KEYCLOAK_GROUP_EMPLOYMENT, KEYCLOAK_GROUP_CV, KEYCLOAK_GROUP_EDUCATION


class Manager(models.Model):
    """
    Минимальная таблица менеджеров для SSO/Keycloak.

    Автоматически создается/обновляется при первом логине пользователя.
    Хранит только необходимый минимум данных для работы системы.
    """

    email = models.EmailField(
        primary_key=True,
        unique=True,
        verbose_name='Email',
        help_text='Email менеджера из Keycloak'
    )
    full_name = models.CharField(
        max_length=255,
        verbose_name='Полное имя',
        help_text='ФИО менеджера'
    )
    username = models.CharField(
        max_length=255,
        verbose_name='Username',
        help_text='Username из Keycloak'
    )
    groups = models.JSONField(
        default=list,
        verbose_name='Группы',
        help_text='Список групп Keycloak (employment-managers, cv-managers и т.д.)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Активен ли менеджер в системе'
    )
    hidden_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата скрытия',
        help_text='Дата и время последнего скрытия менеджера (is_active=False). '
                  'Обнуляется при восстановлении. Используется для автоудаления через 3 месяца.'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        db_table = 'managers'
        verbose_name = 'Менеджер'
        verbose_name_plural = 'Менеджеры'
        ordering = ['full_name']

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    @property
    def is_admin(self):
        """Проверяет, является ли менеджер администратором."""
        return KEYCLOAK_GROUP_ADMIN in self.groups

    @property
    def is_employment_manager(self):
        """Проверяет, является ли менеджер employment-manager."""
        return KEYCLOAK_GROUP_EMPLOYMENT in self.groups

    @property
    def is_cv_manager(self):
        """Проверяет, является ли менеджер cv-manager."""
        return KEYCLOAK_GROUP_CV in self.groups

    @property
    def is_education_manager(self):
        """Проверяет, является ли менеджер education-manager."""
        return KEYCLOAK_GROUP_EDUCATION in self.groups
