from __future__ import annotations

from typing import Any

from core.intern_utils import transliterate_name_to_cyrillic


def _intern_to_dict(intern) -> dict[str, Any]:
    return {
        'id': intern.id,
        'full_name': intern.full_name,
        'email': intern.email or '',
        'group': intern.group or '',
        'manager_email': intern.manager_email or '',
        'direction_id': intern.direction_id,
        'real_interview_date': intern.real_interview_date.isoformat() if intern.real_interview_date else None,
    }


def _serialize_intern_stats_row(item: dict) -> dict[str, Any]:
    return {
        'intern': _intern_to_dict(item['intern']),
        'stats': item['stats'],
        'recent_stats': item['recent_stats'],
        'recent_weeks_data': item['recent_weeks_data'],
        'week_statuses': item['week_statuses'],
        'exclude_from_coefficient': item['exclude_from_coefficient'],
        'status': item['status'],
        'status_display': item['status_display'],
    }


def _serialize_all_months(all_months: dict) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for month, week_list in all_months.items():
        out[month] = [
            {'week_start': s.isoformat(), 'week_end': e.isoformat()}
            for s, e in week_list
        ]
    return out


def _serialize_all_interns_row(row: dict) -> dict[str, Any]:
    return {
        'intern': _intern_to_dict(row['intern']),
        'month': row['month'],
        'month_weeks_data': row['month_weeks_data'],
        'status': row['status'],
        'status_display': row['status_display'],
    }


def serialize_manager_board(manager, context: dict) -> dict[str, Any]:
    """
    Преобразует результат ManagerDetailService.get_context в JSON-совместимый dict.

    Args:
        manager: экземпляр managers.Manager
        context: словарь из ManagerDetailService.get_context
    """
    raw_name = manager.full_name or ''
    display_name = transliterate_name_to_cyrillic(raw_name) or raw_name

    directions = context['directions_dict']
    directions_json = {str(k): v for k, v in directions.items()}

    intern_statuses = context['intern_statuses']
    statuses_json = {str(k): v for k, v in intern_statuses.items()}

    return {
        'manager': {
            'email': manager.email,
            'full_name': display_name,
        },
        'recent_weeks': [list(pair) for pair in context['recent_weeks']],
        'coefficients': context['coefficients'],
        'active_interns': [_serialize_intern_stats_row(x) for x in context['active_interns']],
        'inactive_interns': [_serialize_intern_stats_row(x) for x in context['inactive_interns']],
        'all_months': _serialize_all_months(context['all_months']),
        'all_months_formatted': context['all_months_formatted'],
        'all_interns': [_serialize_all_interns_row(x) for x in context['all_interns']],
        'directions_dict': directions_json,
        'intern_statuses': statuses_json,
    }
