"""
Сериализаторы для API приложения debts.
"""
from decimal import Decimal
from rest_framework import serializers
from directions.models import Direction
from .models import Debt, PaymentHistory


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Сериализатор истории платежей."""

    class Meta:
        model = PaymentHistory
        fields = ['id', 'month', 'year', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']


class DebtListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка долгов (облегчённый).
    Используется в GET /api/debts/.
    Контекст от list(): last_payment_by_debt, payments_four_months_by_debt, row_style_by_debt.
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)
    display_telegram = serializers.SerializerMethodField(read_only=True)
    display_email = serializers.SerializerMethodField(read_only=True)
    last_payment_month = serializers.SerializerMethodField(read_only=True)
    last_payment_year = serializers.SerializerMethodField(read_only=True)
    payments_four_months = serializers.SerializerMethodField(read_only=True)
    row_highlight = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Debt
        fields = [
            'id',
            'intern',
            'intern_name',
            'direction_id',
            'direction_name',
            'display_telegram',
            'display_email',
            'total_amount',
            'paid_amount',
            'balance',
            'payment_status',
            'act_date',
            'last_payment_month',
            'last_payment_year',
            'payments_four_months',
            'row_highlight',
        ]
        read_only_fields = ['balance', 'total_amount']

    def get_direction_name(self, obj):
        """Название направления для списков и карточек."""
        if obj.direction:
            return obj.direction.name
        return None

    def get_display_telegram(self, obj):
        tg = getattr(obj.intern, 'telegram_username', None) or obj.telegram_username
        return (tg or '').strip()

    def get_display_email(self, obj):
        em = getattr(obj.intern, 'email', None) or obj.email
        return (em or '').strip()

    def get_last_payment_month(self, obj):
        lp = (self.context.get('last_payment_by_debt') or {}).get(obj.id)
        return lp[0] if lp else None

    def get_last_payment_year(self, obj):
        lp = (self.context.get('last_payment_by_debt') or {}).get(obj.id)
        return lp[1] if lp else None

    def get_payments_four_months(self, obj):
        raw = (self.context.get('payments_four_months_by_debt') or {}).get(obj.id) or {}
        return {k: str(v) for k, v in raw.items()}

    def get_row_highlight(self, obj):
        return (self.context.get('row_style_by_debt') or {}).get(obj.id, 'default')


class DebtDetailSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор долга с историей платежей.
    Используется в GET /api/debts/{id}/.
    """
    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    payment_history = PaymentHistorySerializer(many=True, read_only=True)
    direction_id = serializers.IntegerField(read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Debt
        fields = [
            'id',
            'intern',
            'intern_name',
            'direction_id',
            'direction_name',
            'telegram_username',
            'email',
            'total_amount',
            'paid_amount',
            'balance',
            'payment_status',
            'act_date',
            'payment_history',
        ]
        read_only_fields = ['balance', 'total_amount']

    def get_direction_name(self, obj):
        """Название направления для списков и карточек."""
        if obj.direction:
            return obj.direction.name
        return None


class DebtCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления долга.
    """
    direction_id = serializers.PrimaryKeyRelatedField(
        source='direction',
        queryset=Direction.objects.all(),
        required=False,
        allow_null=True,
    )
    total_amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        default=Decimal(0),
        min_value=0,
    )

    class Meta:
        model = Debt
        fields = [
            'intern',
            'direction_id',
            'telegram_username',
            'email',
            'total_amount',
            'paid_amount',
            'payment_status',
            'act_date',
        ]


class PaymentHistoryCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для добавления записи о платеже.
    """

    class Meta:
        model = PaymentHistory
        fields = ['month', 'year', 'amount']


class DebtByMonthRowSerializer(serializers.ModelSerializer):
    """Строка отчёта «долги по месяцам» (контекст: meta из resolve_debt_by_month_query + подсветка)."""

    intern_name = serializers.CharField(source='intern.full_name', read_only=True)
    direction_name = serializers.SerializerMethodField(read_only=True)
    payment_status_label = serializers.SerializerMethodField(read_only=True)
    total_period_amount = serializers.SerializerMethodField(read_only=True)
    period_amounts = serializers.SerializerMethodField(read_only=True)
    row_highlight = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Debt
        fields = [
            'id',
            'intern_name',
            'direction_name',
            'total_amount',
            'paid_amount',
            'balance',
            'act_date',
            'payment_status',
            'payment_status_label',
            'total_period_amount',
            'period_amounts',
            'row_highlight',
        ]

    def get_direction_name(self, obj):
        if obj.direction:
            return obj.direction.name
        return None

    def get_payment_status_label(self, obj):
        mapping = {
            'searching': 'Снова ищем',
            'paying': 'Платит',
            'unknown': 'Без статуса',
        }
        return mapping.get(obj.payment_status, 'Без статуса')

    def get_total_period_amount(self, obj):
        totals = self.context.get('total_period_sums') or {}
        v = totals.get(obj.id, 0)
        return str(v)

    def get_period_amounts(self, obj):
        sums = self.context.get('period_sums') or {}
        row = sums.get(obj.id) or {}
        return {k: str(v) for k, v in row.items()}

    def get_row_highlight(self, obj):
        if obj.id in (self.context.get('debts_paid_fully') or set()):
            return 'paid_fully'
        if obj.id in (self.context.get('debts_to_highlight') or set()):
            return 'not_paying'
        return 'default'
