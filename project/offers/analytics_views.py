from django.http import JsonResponse
from django.db import connection
from django.db.models import Avg, Max, Min, Count

from core.constants import MONTH_NAMES
from core.decorators import manager_required_api, cache_analytics
from .models import Offer


def compute_offer_analytics():
    """Вычисляет аналитику по офферам. Вызывается из API-вью и из list-вью для прогрева кэша."""
    # Общие метрики одним запросом
    stats = Offer.objects.aggregate(
        total=Count('id'),
        unique_directions=Count('direction_id', distinct=True),
        avg_amount=Avg('amount'),
        max_amount=Max('amount'),
        min_amount=Min('amount'),
    )

    # Уникальных компаний (исключаем пустые значения и placeholder)
    unique_companies = (
        Offer.objects
        .exclude(company__isnull=True)
        .exclude(company='')
        .exclude(company='—')
        .aggregate(count=Count('company', distinct=True))['count'] or 0
    )

    # Медианный оффер: в PostgreSQL — percentile_cont через cursor, иначе — в Python
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY amount) '
                f'FROM {Offer._meta.db_table} WHERE amount IS NOT NULL'
            )
            row = cursor.fetchone()
        median_offer = float(row[0] or 0) if row else 0
    else:
        amounts = list(
            Offer.objects
            .exclude(amount__isnull=True)
            .order_by('amount')
            .values_list('amount', flat=True)
        )
        median_offer = 0
        if amounts:
            n = len(amounts)
            mid = n // 2
            median_offer = float(
                (amounts[mid - 1] + amounts[mid]) / 2 if n % 2 == 0 else amounts[mid]
            )

    # Самая популярная компания
    popular_company = (
        Offer.objects
        .exclude(company__isnull=True)
        .exclude(company='')
        .exclude(company='—')
        .values('company')
        .annotate(count=Count('company'))
        .order_by('-count')
        .first()
    )

    # Компания с наибольшим средним оффером
    best_company = (
        Offer.objects
        .exclude(company__isnull=True)
        .exclude(company='')
        .exclude(company='—')
        .values('company')
        .annotate(avg_amount=Avg('amount'))
        .order_by('-avg_amount')
        .first()
    )

    # Лучший месяц по среднему
    best_month = (
        Offer.objects
        .values('year', 'month')
        .annotate(avg_amount=Avg('amount'))
        .order_by('-avg_amount')
        .first()
    )
    best_month_name = '—'
    if best_month:
        try:
            month_name = MONTH_NAMES[best_month['month'] - 1]
            best_month_name = f"{month_name} {best_month['year']}"
        except (IndexError, TypeError):
            best_month_name = f"{best_month['month']}/{best_month['year']}"

    data = {
        'total': stats['total'],
        'directions': stats['unique_directions'] or 0,
        'companies': unique_companies,
        'avg-offer': round(float(stats['avg_amount'] or 0), 2),
        'median-offer': round(float(median_offer), 2),
        'max-offer': float(stats['max_amount']) if stats['max_amount'] else 0,
        'min-offer': float(stats['min_amount']) if stats['min_amount'] else 0,
        'popular-company': popular_company['company'] if popular_company else '—',
        'best-company': best_company['company'] if best_company else '—',
        'best-month': best_month_name,
        'tooltips': {
            'total': 'За все время ведения таблицы (с 02.2025 по сей день).',
            'directions': 'Всего направлений в таблице.',
            'companies': 'Уникальных компаний в таблице.',
            'avg-offer': 'Средний оффер.',
            'median-offer': 'Медианный оффер.',
            'max-offer': 'Максимальный оффер.',
            'min-offer': 'Минимальный оффер.',
            'popular-company': 'Которая чаще всего встречается и разработчики туда получают офферы.',
            'best-company': 'Самые большие офферы в компании.',
            'best-month': 'Лучший месяц по сумме офферов.',
        }
    }
    return data


@manager_required_api
@cache_analytics()
def offer_analytics_api(request):
    """Возвращает JSON с аналитикой по офферам."""
    return JsonResponse(compute_offer_analytics())
