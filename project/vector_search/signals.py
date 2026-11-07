import logging
import os

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from companies.models import Company
from directions.models import Direction
from employees.models import InternWeeklyStatus
from interviews.models import Interview
from interns.models import Intern
from offers.models import Offer
from debts.models import Debt
from sad_intern.models import SadIntern
from managers.models import Manager

from vector_search.tasks import update_embedding_task, delete_embedding_task
from knowledge_base_app.models import KBArticle

from vector_search.utils import (
    ENTITY_COMPANY,
    ENTITY_DEBT,
    ENTITY_DIRECTION,
    ENTITY_INTERN,
    ENTITY_INTERN_WEEKLY_STATUS,
    ENTITY_INTERVIEW,
    ENTITY_KB_ARTICLE,
    ENTITY_MANAGER,
    ENTITY_OFFER,
    ENTITY_SAD_INTERN,
)

logger = logging.getLogger('vector_search.signals')


def _schedule_update(entity_type: str, entity_id, created: bool = False):
    if os.environ.get('DISABLE_VECTOR_SIGNALS'):
        return
    action = 'создан' if created else 'обновлён'
    logger.info(f'Сигнал post_save [{entity_type}#{entity_id}] — объект {action}, задача векторизации отправлена')
    update_embedding_task.delay(entity_type, entity_id)


def _schedule_delete(entity_type: str, entity_id):
    if os.environ.get('DISABLE_VECTOR_SIGNALS'):
        return
    logger.info(f'Сигнал post_delete [{entity_type}#{entity_id}] — задача удаления эмбеддинга отправлена')
    delete_embedding_task.delay(entity_type, entity_id)


@receiver(post_save, sender=Interview)
def interview_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_INTERVIEW, instance.id, created)


@receiver(post_delete, sender=Interview)
def interview_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_INTERVIEW, instance.id)


@receiver(post_save, sender=Intern)
def intern_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_INTERN, instance.id, created)


@receiver(post_delete, sender=Intern)
def intern_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_INTERN, instance.id)


@receiver(post_save, sender=Offer)
def offer_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_OFFER, instance.id, created)


@receiver(post_delete, sender=Offer)
def offer_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_OFFER, instance.id)


@receiver(post_save, sender=Debt)
def debt_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_DEBT, instance.id, created)


@receiver(post_delete, sender=Debt)
def debt_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_DEBT, instance.id)


@receiver(post_save, sender=SadIntern)
def sad_intern_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_SAD_INTERN, instance.id, created)


@receiver(post_delete, sender=SadIntern)
def sad_intern_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_SAD_INTERN, instance.id)


@receiver(post_save, sender=Manager)
def manager_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_MANAGER, instance.email, created)


@receiver(post_delete, sender=Manager)
def manager_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_MANAGER, instance.email)


@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_COMPANY, instance.id, created)


@receiver(post_delete, sender=Company)
def company_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_COMPANY, instance.id)


@receiver(post_save, sender=Direction)
def direction_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_DIRECTION, instance.id, created)


@receiver(post_delete, sender=Direction)
def direction_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_DIRECTION, instance.id)


@receiver(post_save, sender=InternWeeklyStatus)
def intern_weekly_status_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_INTERN_WEEKLY_STATUS, instance.id, created)


@receiver(post_delete, sender=InternWeeklyStatus)
def intern_weekly_status_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_INTERN_WEEKLY_STATUS, instance.id)


@receiver(post_save, sender=KBArticle)
def kb_article_post_save(sender, instance, created, **kwargs):
    _schedule_update(ENTITY_KB_ARTICLE, instance.pk, created)


@receiver(post_delete, sender=KBArticle)
def kb_article_post_delete(sender, instance, **kwargs):
    _schedule_delete(ENTITY_KB_ARTICLE, instance.pk)
