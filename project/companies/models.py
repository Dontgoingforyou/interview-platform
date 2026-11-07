from django.db import models


class Company(models.Model):
    """ Компания, в которую проходит собеседование студент. """
    name = models.CharField(max_length=255, verbose_name='Название', db_index=True)
    is_bigtech = models.BooleanField(default=False, verbose_name='Бигтех')
    aliases = models.TextField(
        blank=True,
        default='',
        verbose_name='Псевдонимы',
        help_text='Варианты написания названия (по одному на строку). Используются при автоматическом импорте.',
    )

    class Meta:
        db_table = 'companies_company'
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_aliases_list(self):
        """ Возвращает список псевдонимов (непустые строки). """
        return [line.strip() for line in self.aliases.splitlines() if line.strip()]
