import logging
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q

from interviews.models import Interview

from .models import Company

logger = logging.getLogger('companies')


@dataclass(frozen=True)
class MergeCompaniesResult:
    """Результат объединения дублей в одну компанию."""

    primary_id: int
    primary_name: str
    duplicate_ids: list[int]
    duplicate_names: list[str]
    interviews_moved: int


class MergeCompaniesService:
    """
    Объединение дублей: перенос собеседований, слияние псевдонимов, удаление дублей.
    Вызывать внутри view после валидации формы / тела запроса.
    """

    @staticmethod
    def execute(primary: Company, duplicates: list[Company]) -> MergeCompaniesResult:
        """
        Args:
            primary: Главная компания (остаётся в БД).
            duplicates: Список дублей (без primary), будут удалены.

        Raises:
            IntegrityError: при сбое сохранения в БД.
        """
        dup_ids = [c.pk for c in duplicates]
        dup_names: list[str] = []
        new_aliases_lines = list(primary.get_aliases_list())
        total_interviews_moved = 0

        with transaction.atomic():
            for dup in duplicates:
                moved = dup.interview_set.all().update(company=primary)
                total_interviews_moved += moved

                if dup.name not in new_aliases_lines and dup.name != primary.name:
                    new_aliases_lines.append(dup.name)

                for alias in dup.get_aliases_list():
                    if alias not in new_aliases_lines and alias != primary.name:
                        new_aliases_lines.append(alias)

                dup_names.append(dup.name)

            primary.aliases = '\n'.join(new_aliases_lines)
            primary.save(update_fields=['aliases'])

            Company.objects.filter(pk__in=dup_ids).delete()

        return MergeCompaniesResult(
            primary_id=primary.pk,
            primary_name=primary.name,
            duplicate_ids=dup_ids,
            duplicate_names=dup_names,
            interviews_moved=total_interviews_moved,
        )


def compute_company_list_stats():
    """Агрегаты для шапки списка компаний."""
    stats = (
        Company.objects.annotate(
            has_interview=Exists(Interview.objects.filter(company_id=OuterRef('pk'))),
        ).aggregate(
            total_count=Count('id'),
            bigtech_count=Count('id', filter=Q(is_bigtech=True)),
            with_interviews_count=Count('id', filter=Q(has_interview=True)),
        )
    )
    total = stats['total_count']
    with_iv = stats['with_interviews_count']
    return {
        'total_count': total,
        'bigtech_count': stats['bigtech_count'],
        'with_interviews_count': with_iv,
        'without_interviews_count': total - with_iv,
    }
