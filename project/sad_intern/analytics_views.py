from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from core.decorators import manager_required_api, cache_analytics
from .models import SadIntern


def compute_sad_intern_analytics():
    """Вычисляет аналитику грустящих студентов. Вызывается из API-вью и из list-вью для прогрева кэша."""
    base_qs = SadIntern.objects.for_main_waiting_list()

    # Общие метрики одним aggregate
    agg = base_qs.aggregate(
        total=Count('id'),
        with_telegram=Count('id', filter=Q(
            telegram_username__isnull=False
        ) & ~Q(telegram_username='')),
        avg_wait=Avg('days_waiting'),
    )
    total_sad_interns = agg['total']
    with_telegram = agg['with_telegram']
    avg_wait = agg['avg_wait'] or 0

    # Максимальное ожидание и кто дольше всех ждёт
    # ОПТИМИЗАЦИЯ: Добавляем select_related для избежания дополнительного запроса
    longest_wait_record = base_qs.select_related('intern').order_by('-days_waiting').first()
    longest_wait_days = longest_wait_record.days_waiting if longest_wait_record else 0
    longest_wait_name = longest_wait_record.intern.full_name if longest_wait_record else '—'

    data = {
        'total': total_sad_interns,
        'with_contact': with_telegram,
        'avg_wait': round(avg_wait, 2),
        'longest_wait_days': longest_wait_days,
        'longest_wait_name': longest_wait_name,
        'tooltips': {
            'total': 'Общее количество грустящих студентов.',
            'with-contact': 'Количество грустящих студентов с контактом в Telegram.',
            'avg-wait': 'Среднее количество дней ожидания собеседования.',
            'longest': 'Студент, который долго ждёт собеседование.',
        }
    }
    return data


@manager_required_api
@cache_analytics()
def sad_intern_analytics_api(request):
    """Возвращает JSON с аналитикой по 'грустящим' студентами."""
    return JsonResponse(compute_sad_intern_analytics())
