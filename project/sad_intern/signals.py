from django.db.models.signals import post_save
from django.dispatch import receiver
from interns.models import Intern
from core.constants import SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE
from .models import SadIntern
from core.logging_mixins import log_signal
import logging

logger = logging.getLogger('sad_intern.sadintern')


def _intern_eligible_for_auto_sad_intern(instance: Intern) -> bool:
    """Условия автосоздания/автообновления SadIntern (только сигнал, не списки)."""
    if not instance.real_interview_date:
        return False
    if instance.real_interview_date < SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE:
        return False
    email = (instance.manager_email or '').strip()
    if not email:
        return False
    return True


@receiver(post_save, sender=Intern)
@log_signal('post_save', 'sad_intern.sadintern')
def auto_create_or_update_sad_intern(sender, instance, created, **kwargs):
    """
    Создаёт или обновляет SadIntern только если у интерна есть менеджер и дата выхода на собесы
    не раньше SAD_INTERN_ELIGIBLE_MIN_REAL_INTERVIEW_DATE.

    Если условия не выполнены — существующую запись не изменяем (grandfathering).
    """
    if not _intern_eligible_for_auto_sad_intern(instance):
        return

    waiting_since = instance.real_interview_date
    sad_intern = SadIntern.objects.filter(intern=instance).first()

    if sad_intern:
        old_waiting = sad_intern.waiting_since
        sad_intern.waiting_since = waiting_since
        sad_intern.telegram_username = instance.telegram_username or sad_intern.telegram_username
        sad_intern.manager_email = instance.manager_email or sad_intern.manager_email
        sad_intern.save()

        logger.info(
            f"[ОБНОВЛЕНИЕ SadIntern] ID: {sad_intern.id} | "
            f"waiting_since: {old_waiting} → {sad_intern.waiting_since} | "
            f"days_waiting: {sad_intern.days_waiting}"
        )
    else:
        new_sad = SadIntern.objects.create(
            intern=instance,
            waiting_since=waiting_since,
            telegram_username=instance.telegram_username,
            manager_email=instance.manager_email,
        )
        logger.info(
            f"[СОЗДАНИЕ SadIntern] Новая запись для {instance.full_name} | "
            f"ID: {new_sad.id} | waiting_since: {waiting_since}"
        )
