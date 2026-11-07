from typing import cast

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import F, Q, QuerySet

from directions.models import Direction

from core.constants import SAD_INTERN_STATUS_ON_PROJECT
from .managers import SadInternQuerySet
from .models import SadIntern

GROUPS_PER_PAGE = 3
PER_GROUP_PAGINATE_BY = 10
ON_PROJECT_PAGE_SIZE = 20

ORDER_FIELD_MAP = {
    'id': 'id',
    'full_name': 'intern__full_name',
    'date_joined': 'intern__real_interview_date',
    'days_waiting': 'days_waiting',
    'telegram': 'telegram_username',
    'status': 'status',
    'manager': 'intern__manager_email',
}


def sad_intern_role_scoped_qs(user) -> QuerySet:
    """Админ, HR, outstaff — все записи; менеджер — только manager_email = email."""
    qs = SadIntern.objects.select_related('intern', 'intern__direction')
    if getattr(user, 'is_admin', False):
        return qs
    if getattr(user, 'is_hr', False) or getattr(user, 'is_outstaff', False):
        return qs
    email = getattr(user, 'email', None)
    if email:
        return qs.filter(manager_email=email)
    return qs.none()


def apply_q_search(qs: QuerySet, query: str | None) -> tuple[QuerySet, list[int] | None]:
    """Фильтр по q; возвращает (qs, direction_ids для on_project) или None если q пустой."""
    if not query or not str(query).strip():
        return qs, None
    q = str(query).strip()
    direction_ids = list(
        Direction.objects.filter(name__icontains=q).values_list('id', flat=True)
    )
    qs = qs.filter(
        Q(intern__full_name__icontains=q)
        | Q(telegram_username__icontains=q)
        | Q(note__icontains=q)
        | Q(intern__direction_id__in=direction_ids)
    )
    return qs, direction_ids


def apply_list_filters(
    qs: QuerySet,
    params,
    *,
    waiting: bool,
    allow_manager_email_filter: bool = False,
) -> QuerySet:
    """
    waiting=True: основной список (без on_project, с exclude_left_interns).
    waiting=False: только on_project (без exclude_left — как legacy get_context_data).
    """
    if waiting:
        qs = (
            cast(SadInternQuerySet, qs)
            .exclude(status=SAD_INTERN_STATUS_ON_PROJECT)
            .exclude_left_interns()
        )
    else:
        qs = qs.filter(status=SAD_INTERN_STATUS_ON_PROJECT)

    qs, _ = apply_q_search(qs, params.get('q'))

    status_filter = params.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    direction_filter = params.get('direction')
    if direction_filter:
        try:
            qs = qs.filter(intern__direction_id=int(direction_filter))
        except (ValueError, TypeError):
            pass

    if allow_manager_email_filter:
        manager_filter = params.get('manager_email') or params.get('manager')
        if manager_filter and '@' in str(manager_filter):
            qs = qs.filter(manager_email=str(manager_filter))

    return qs


def apply_ordering(qs: QuerySet, order_by: str | None, order_dir: str | None) -> QuerySet:
    order_by = order_by or 'days_waiting'
    order_dir = (order_dir or 'desc').lower()
    field = ORDER_FIELD_MAP.get(order_by)
    if not field:
        order_by = 'days_waiting'
        field = ORDER_FIELD_MAP['days_waiting']
    if order_dir == 'desc':
        return qs.order_by(F(field).desc(nulls_last=True))
    return qs.order_by(F(field).asc(nulls_last=True))


def get_unique_direction_groups(qs: QuerySet) -> list[tuple[int | None, str]]:
    """Список (direction_id, direction_name), сортировка по имени; None = без направления."""
    direction_ids = list(qs.values_list('intern__direction_id', flat=True).distinct())
    unique_ids = [did for did in direction_ids if did is not None]
    names: dict[int | None, str] = {}
    if unique_ids:
        for d in Direction.objects.filter(id__in=unique_ids):
            names[d.id] = d.name
    for did in unique_ids:
        if did not in names:
            names[did] = f'Направление {did}'
    if qs.filter(intern__direction_id__isnull=True).exists():
        names[None] = 'Без направления'
    pairs = [(did, names[did]) for did in names]
    return sorted(pairs, key=lambda x: x[1])


def build_group_q(groups_to_show: list[tuple[int | None, str]]) -> Q:
    direction_filters = Q()
    for direction_id, _name in groups_to_show:
        if direction_id is None:
            direction_filters |= Q(intern__direction_id__isnull=True)
        else:
            direction_filters |= Q(intern__direction_id=direction_id)
    return direction_filters


def pagination_key_for_direction(direction_id: int | None) -> str:
    did = direction_id if direction_id is not None else 'none'
    return f'page_{did}'


def build_grouped_payload(
    qs: QuerySet,
    params,
    *,
    groups_per_page: int = GROUPS_PER_PAGE,
    per_group: int = PER_GROUP_PAGINATE_BY,
) -> dict:
    """
    Группированный ответ для ожидающих (без on_project).
    params: directions_offset, page_<id|none>, order_by, order_dir, ...
    """
    unique_groups = get_unique_direction_groups(qs)
    total_directions = len(unique_groups)

    try:
        offset = int(params.get('directions_offset', 0) or 0)
    except (ValueError, TypeError):
        offset = 0
    offset = max(0, offset)

    groups_to_show = unique_groups[offset : offset + groups_per_page]
    next_offset = offset + len(groups_to_show)
    has_more_directions = next_offset < total_directions

    if not groups_to_show:
        return {
            'groups': [],
            'has_more_directions': False,
            'next_directions_offset': None,
            'total_directions': total_directions,
            'directions_offset': offset,
        }

    filtered = qs.filter(build_group_q(groups_to_show))
    order_by = params.get('order_by')
    order_dir = params.get('order_dir')
    filtered = apply_ordering(filtered, order_by, order_dir)

    # Группировка объектов по ключу направления (порядок в groups_to_show)
    grouped_lists: dict[tuple[int | None, str], list] = {k: [] for k in groups_to_show}
    for obj in filtered:
        key = _match_group_key(obj, groups_to_show)
        if key in grouped_lists:
            grouped_lists[key].append(obj)

    groups_out = []
    for group_key in groups_to_show:
        direction_id, direction_name = group_key
        objects = grouped_lists.get(group_key, [])
        pag_key = pagination_key_for_direction(direction_id)
        try:
            page_num = int(params.get(pag_key, 1) or 1)
        except (ValueError, TypeError):
            page_num = 1
        page_num = max(1, page_num)

        if len(objects) > per_group:
            paginator = Paginator(objects, per_group)
            try:
                page_obj = paginator.page(page_num)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
            page_items = list(page_obj.object_list)
            total_pages = paginator.num_pages
            current_page = page_obj.number
            total_count = paginator.count
        else:
            page_items = objects
            total_pages = 1
            current_page = 1
            total_count = len(objects)

        groups_out.append(
            {
                'direction_id': direction_id,
                'direction_name': direction_name,
                'page': current_page,
                'total_pages': total_pages,
                'total_count': total_count,
                'per_page': per_group,
                'pagination_key': pag_key,
                'results': page_items,
            }
        )

    return {
        'groups': groups_out,
        'has_more_directions': has_more_directions,
        'next_directions_offset': next_offset if has_more_directions else None,
        'total_directions': total_directions,
        'directions_offset': offset,
    }


def _match_group_key(obj, groups_to_show: list[tuple[int | None, str]]) -> tuple[int | None, str]:
    did = obj.intern.direction_id if obj.intern else None
    for g in groups_to_show:
        gid, _name = g
        if gid == did:
            return g
    return groups_to_show[0] if groups_to_show else (None, 'Без направления')


def build_on_project_page(qs: QuerySet, params) -> dict:
    """Пагинированный список on_project (после фильтров, порядок как в SadInternListView: -date_added)."""
    qs = qs.order_by('-date_added')
    paginator = Paginator(qs, ON_PROJECT_PAGE_SIZE)
    try:
        page_num = int(params.get('on_project_page', 1) or 1)
    except (ValueError, TypeError):
        page_num = 1
    try:
        page_obj = paginator.page(page_num)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return {
        'count': paginator.count,
        'page': page_obj.number,
        'total_pages': paginator.num_pages,
        'results': list(page_obj.object_list),
    }
