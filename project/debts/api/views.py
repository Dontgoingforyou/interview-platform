from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsManagerOrAdmin
from core.logging_mixins import ApiCRUDLoggingMixin, get_user_label_for_log
from core.pagination import ListPagination

from ..drf_by_month import highlight_sets_for_page, resolve_debt_by_month_query
from ..drf_list_query import apply_debt_list_filters, apply_debt_list_ordering
from ..models import Debt, PaymentHistory
from ..serializers import (
    DebtByMonthRowSerializer,
    DebtCreateUpdateSerializer,
    DebtDetailSerializer,
    DebtListSerializer,
    PaymentHistoryCreateSerializer,
)


class DebtViewSet(ApiCRUDLoggingMixin, viewsets.ModelViewSet):
    """
    ViewSet для управления долгами студентов.

    Администраторы видят все долги.
    Менеджеры видят долги своих студентов (через intern.manager_email).
    """

    api_logger_name = 'debts.debt'
    pagination_class = ListPagination

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'add_payment', 'destroy'):
            return [IsAdminRole()]
        return [IsManagerOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DebtDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return DebtCreateUpdateSerializer
        if self.action == 'by_month':
            return DebtByMonthRowSerializer
        return DebtListSerializer

    def _role_scoped_base_qs(self):
        qs = Debt.objects.select_related('intern', 'direction')
        user = self.request.user
        if not getattr(user, 'is_admin', False):
            email = getattr(user, 'email', None)
            if email:
                qs = qs.filter(intern__manager_email=email)
        return qs

    def get_queryset(self):
        qs = self._role_scoped_base_qs()

        if self.action == 'retrieve':
            return qs.prefetch_related('payment_history')

        if self.action == 'list':
            qs = apply_debt_list_filters(qs, self.request.query_params)
            qs = apply_debt_list_ordering(qs, self.request.query_params)

        return qs

    def _list_payment_context(self, debts):
        """Данные по платежам для текущей страницы списка (последние 4 мес., подсветка)."""
        debt_ids = [d.id for d in debts]
        if not debt_ids:
            return {
                'last_payment_by_debt': {},
                'payments_four_months_by_debt': {},
                'row_style_by_debt': {},
                'last_four_month_labels': [],
            }

        today = date.today()
        last_4_months = []
        for i in range(4):
            month_date = today - relativedelta(months=i)
            last_4_months.append(
                {
                    'label': month_date.strftime('%m/%y'),
                    'year': month_date.year,
                    'month': month_date.month,
                }
            )
        last_4_months.reverse()
        labels = [m['label'] for m in last_4_months]

        payment_filters = Q()
        for m in last_4_months:
            payment_filters |= Q(debt_id__in=debt_ids, year=m['year'], month=m['month'])

        all_payments = (
            PaymentHistory.objects.filter(debt_id__in=debt_ids)
            .order_by('debt_id', '-year', '-month')
            .values('debt_id', 'month', 'year')
        )
        last_payment_by_debt = {}
        seen = set()
        for p in all_payments:
            did = p['debt_id']
            if did not in seen:
                last_payment_by_debt[did] = (p['month'], p['year'])
                seen.add(did)

        payments_summary = (
            PaymentHistory.objects.filter(payment_filters)
            .values('debt_id', 'year', 'month')
            .annotate(total=Sum('amount'))
        )
        payments_four_months_by_debt = {did: {} for did in debt_ids}
        for p in payments_summary:
            did = p['debt_id']
            label = f"{p['month']:02d}/{p['year'] % 100:02d}"
            payments_four_months_by_debt[did][label] = p['total'] or 0

        payment_filters_4m = Q()
        for m in last_4_months:
            payment_filters_4m |= Q(year=m['year'], month=m['month'])
        debts_with_payments_4m = set(
            PaymentHistory.objects.filter(debt_id__in=debt_ids)
            .filter(payment_filters_4m)
            .values_list('debt_id', flat=True)
            .distinct()
        )
        act_threshold = today - relativedelta(months=3)
        row_style_by_debt = {}
        for d in debts:
            if d.balance == 0:
                row_style_by_debt[d.id] = 'paid_fully'
            elif (
                d.id not in debts_with_payments_4m
                and d.balance != 0
                and d.act_date
                and d.act_date < act_threshold
            ):
                row_style_by_debt[d.id] = 'not_paying'
            else:
                row_style_by_debt[d.id] = 'default'

        return {
            'last_payment_by_debt': last_payment_by_debt,
            'payments_four_months_by_debt': payments_four_months_by_debt,
            'row_style_by_debt': row_style_by_debt,
            'last_four_month_labels': labels,
        }

    @extend_schema(
        summary='Список долгов',
        description=(
            'Список долгов студентов с пагинацией (page, page_size).\n\n'
            'Менеджер видит долги только своих студентов.\n\n'
            '**Фильтры:** `q` или `search`, `direction`, `payment_status`, '
            '`intern_id`, `not_paid_filter=3months`, `act_date_filter`, `act_date_from`, '
            '`act_date_to`; сортировка `order_by`, `order_dir`.'
        ),
        tags=['Долги'],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        debts = list(page) if page is not None else list(queryset)
        pay_ctx = self._list_payment_context(debts)
        serializer = self.get_serializer(
            debts,
            many=True,
            context={**self.get_serializer_context(), **pay_ctx},
        )
        if page is not None:
            response = self.get_paginated_response(serializer.data)
            response.data['last_four_month_labels'] = pay_ctx['last_four_month_labels']
            return response
        return Response(
            {
                'results': serializer.data,
                'last_four_month_labels': pay_ctx['last_four_month_labels'],
            }
        )

    @extend_schema(
        summary='Долги по месяцам',
        description=(
            'Отчёт по платежам за период. Обязательны `month_from`, `year_from`, `month_to`, `year_to`. '
            'Опционально `payment_status_filter`: paying | not_paying | paid_fully.'
        ),
        tags=['Долги'],
    )
    @action(detail=False, methods=['get'], url_path='by-month')
    def by_month(self, request):
        base = self._role_scoped_base_qs()
        resolved = resolve_debt_by_month_query(base, request.query_params)
        if not resolved['ok']:
            return Response({'detail': resolved['error']}, status=resolved['status'])

        qs = resolved['qs']
        meta = resolved['meta']
        page = self.paginate_queryset(qs)
        debts = list(page) if page is not None else list(qs)

        hl = highlight_sets_for_page(debts, meta['month_to'], meta['year_to'])
        serializer = self.get_serializer(
            debts,
            many=True,
            context={
                **self.get_serializer_context(),
                'period_sums': meta['period_sums'],
                'total_period_sums': meta['total_period_sums'],
                'debts_paid_fully': hl['debts_paid_fully'],
                'debts_to_highlight': hl['debts_to_highlight'],
            },
        )

        payload = {
            'export_months': meta['export_months'],
            'selected_period': meta['selected_period'],
        }
        if page is not None:
            response = self.get_paginated_response(serializer.data)
            for k, v in payload.items():
                response.data[k] = v
            return response
        return Response({**payload, 'results': serializer.data})

    @extend_schema(
        summary='Детали долга',
        description='Возвращает полную информацию о долге, включая историю платежей.',
        tags=['Долги'],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary='Создать долг',
        description='Создаёт новую запись о долге студента. Только для администраторов.',
        tags=['Долги'],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить долг (PUT)',
        description='Полное обновление записи о долге. Только для администраторов.',
        tags=['Долги'],
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Обновить долг',
        description='Частичное обновление записи о долге. Только для администраторов.',
        tags=['Долги'],
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary='Удалить долг',
        description='Удаление записи о долге. Только для администраторов.',
        tags=['Долги'],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary='Добавить платёж',
        description='Добавляет запись о платеже в историю долга. Только для администраторов.',
        request=PaymentHistoryCreateSerializer,
        tags=['Долги'],
    )
    @action(detail=True, methods=['post'], url_path='add-payment')
    def add_payment(self, request, pk=None):
        """Добавляет запись о платеже к долгу и обновляет paid_amount."""
        from django.db import transaction

        debt = self.get_object()
        serializer = PaymentHistoryCreateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                payment = PaymentHistory.objects.create(debt=debt, **serializer.validated_data)
                debt.paid_amount += payment.amount
                debt.save(update_fields=['paid_amount', 'balance'])
            self._get_api_logger().info(
                'API [ПЛАТЁЖ] долг id=%s — %s', debt.pk, get_user_label_for_log(request),
            )
            return Response(
                {'message': 'Платёж успешно добавлен.'},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
