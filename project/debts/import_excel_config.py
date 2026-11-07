"""Конфигурация колонок для импорта долгов из Excel/CSV (раньше на DebtImportView)."""

REQUIRED_COLUMNS = ['full_name']

COLUMN_MAPPING = {
    'Направление': 'direction_name',
    'ФИО': 'full_name',
    'тг': 'telegram_username',
    '@': 'email',
    'Общая сумма': 'total_amount_raw',
    'Сколько уже заплатил': 'paid_amount_raw',
    'Сколько еще осталось': 'balance_raw',
    'Дата акта': 'act_date_str',
    'НДС 5%': 'vat_status',
}
