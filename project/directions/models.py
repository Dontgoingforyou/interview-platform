from django.db import models


class Direction(models.Model):
    """ Направление обучения/специализации студента. """
    name = models.CharField(max_length=255, verbose_name='Название')

    class Meta:
        db_table = 'directions_direction'
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'
        ordering = ['name']

    def __str__(self):
        return self.name
