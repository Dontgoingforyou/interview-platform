"""
API-эндпоинты для админ-отчётов employees (KPI, количество разработчиков).

GET /api/employees/admin/kpi/         — отчёт KPI за период (только admin)
GET /api/employees/admin/developers/   — количество активных разработчиков у менеджеров (только admin)
"""
from datetime import datetime

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole
from core.intern_utils import transliterate_name_to_cyrillic

from ..services import get_developer_count_data, get_kpi_report_data


def _serialize_manager(manager):
    """Сериализация менеджера для JSON (full_name — для отображения, латиница → кириллица)."""
    raw = manager.full_name or ''
    display_name = transliterate_name_to_cyrillic(raw) or raw
    return {
        'full_name': display_name,
        'email': manager.email,
        'is_active': manager.is_active,
    }


def _serialize_intern(intern):
    """Сериализация студента для JSON."""
    return {
        'id': intern.id,
        'full_name': intern.full_name,
        'email': intern.email or '',
        'group': intern.group or '',
        'manager_email': intern.manager_email or '',
    }


class AdminKpiReportAPIView(APIView):
    """Отчёт KPI: менеджеры с KPI >= порога за период. Только для администраторов."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]

    @extend_schema(
        summary='Отчёт KPI за период',
        description=(
            'Возвращает менеджеров, у которых KPI (среднее число собеседований на активного студента '
            'в неделю) не ниже заданного порога за выбранный период.\n\n'
            '**Параметры:** date_from, date_to (YYYY-MM-DD), min_kpi (по умолчанию 3).'
        ),
        parameters=[
            OpenApiParameter('date_from', OpenApiTypes.DATE, required=True,
                             description='Начало периода (YYYY-MM-DD)'),
            OpenApiParameter('date_to', OpenApiTypes.DATE, required=True,
                             description='Конец периода (YYYY-MM-DD)'),
            OpenApiParameter('min_kpi', OpenApiTypes.NUMBER, required=False, default=3,
                             description='Минимальный порог KPI'),
        ],
        tags=['Сотрудники'],
        responses={
            200: {'description': 'Успешно'},
            400: {'description': 'Некорректные параметры или период'},
        },
    )
    def get(self, request):
        date_from_str = request.query_params.get('date_from', '')
        date_to_str = request.query_params.get('date_to', '')
        min_kpi_str = request.query_params.get('min_kpi', '3')

        if not date_from_str or not date_to_str:
            return Response(
                {'error': 'Укажите date_from и date_to (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            min_kpi = float(min_kpi_str) if min_kpi_str else 3.0
        except ValueError:
            return Response(
                {'error': 'Некорректный формат даты или порога KPI'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = get_kpi_report_data(date_from, date_to, min_kpi)
        if 'error' in data:
            return Response({'error': data['error']}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        for item in data['results']:
            results.append({
                'manager': _serialize_manager(item['manager']),
                'qualifying_weeks_count': item['qualifying_weeks_count'],
                'qualifying_weeks': item['qualifying_weeks'],
                'total_active_devs': item['total_active_devs'],
            })

        return Response({
            'date_from': date_from_str,
            'date_to': date_to_str,
            'min_kpi': min_kpi,
            'results': results,
        }, status=status.HTTP_200_OK)


class AdminDeveloperCountAPIView(APIView):
    """Отчёт: количество активных разработчиков у каждого менеджера. Только для администраторов."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]

    @extend_schema(
        summary='Количество разработчиков по менеджерам',
        description=(
            'Возвращает список менеджеров с количеством активных студентов и списком студентов.\n\n'
            '**Параметр:** show_hidden=1 — включить неактивных менеджеров.'
        ),
        parameters=[
            OpenApiParameter('show_hidden', OpenApiTypes.BOOL, required=False, default=False,
                             description='Включить неактивных менеджеров'),
        ],
        tags=['Сотрудники'],
        responses={200: {'description': 'Успешно'}},
    )
    def get(self, request):
        show_hidden = request.query_params.get('show_hidden', '').lower() in ('1', 'true', 'yes')
        data = get_developer_count_data(show_hidden)

        results = []
        for item in data['results']:
            results.append({
                'manager': _serialize_manager(item['manager']),
                'active_count': item['active_count'],
                'interns': [_serialize_intern(i) for i in item['interns']],
            })

        hidden_results = []
        for item in data['hidden_results']:
            hidden_results.append({
                'manager': _serialize_manager(item['manager']),
                'active_count': item['active_count'],
                'interns': [_serialize_intern(i) for i in item['interns']],
            })

        return Response({
            'results': results,
            'hidden_results': hidden_results,
            'total_active': data['total_active'],
            'hidden_count': data['hidden_count'],
        }, status=status.HTTP_200_OK)
