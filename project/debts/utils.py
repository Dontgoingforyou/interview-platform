import re
import logging
import pandas as pd

logger = logging.getLogger('debts_import')


def parse_money_string(money_str):
    """
    Преобразует строку с денежным значением в float.
    Обрабатывает различные форматы: пробелы, запятые, точки как разделители тысяч.
    """
    if pd.isna(money_str):
        return 0.0

    original_value = str(money_str)
    money_str = str(money_str).strip()
    if not money_str or money_str.lower() in ['nan', 'none', '<na>', '']:
        return 0.0

    # Удаляем валютные символы и текст
    money_str = re.sub(r'[ррRr]\.?\s*', '', money_str, flags=re.IGNORECASE)
    money_str = money_str.strip()

    # Если строка пустая после очистки
    if not money_str:
        return 0.0

    # Удаляем все типы пробелов (включая неразрывные пробелы и другие Unicode пробелы)
    # Используем regex для удаления всех пробельных символов
    money_str = re.sub(r'\s+', '', money_str)

    # Определяем, есть ли десятичная часть (точка или запятая перед последними 1-3 цифрами)
    # Паттерн: цифры, затем точка/запятая, затем 1-3 цифры в конце
    has_decimal = bool(re.search(r'[.,]\d{1,3}$', money_str))

    if has_decimal:
        # Есть десятичная часть - заменяем запятую на точку, удаляем остальные разделители
        # Сначала заменяем запятую на точку, если она используется как десятичный разделитель
        if ',' in money_str and money_str.rindex(',') > len(money_str) - 4:
            # Запятая в конце - это десятичный разделитель
            money_str = money_str.replace(',', '.')
        # Удаляем все разделители тысяч (точки и запятые, кроме последней точки)
        # Удаляем все точки кроме последней
        if money_str.count('.') > 1:
            parts = money_str.rsplit('.', 1)
            # Удаляем все нецифровые символы кроме точки из первой части
            money_str = re.sub(r'[^\d]', '', parts[0]) + '.' + parts[1]
        else:
            # Удаляем все нецифровые символы кроме точки
            money_str = re.sub(r'[^\d.]', '', money_str)
    else:
        # Нет десятичной части - удаляем все нецифровые символы
        money_str = re.sub(r'[^\d]', '', money_str)

    # Проверяем, что остались только цифры и возможно одна точка
    if not money_str or not re.match(r'^\d+\.?\d*$', money_str):
        logger.warning(f"Не удалось распознать денежное значение: '{original_value}' (после обработки: '{money_str}')")
        return 0.0

    try:
        result = float(money_str)
        return result
    except ValueError:
        logger.warning(f"Не удалось распознать денежное значение: '{original_value}' (после обработки: '{money_str}')")
        return 0.0


def find_payment_columns(columns):
    """
    Находит столбцы, соответствующие месяцам/годам.
    Возвращает список названий столбцов.
    """
    payment_cols = []
    for col in columns:
        col_str = str(col).strip()
        # Паттерн для MM/YY
        if re.match(r'^\d{2}/\d{2}$', col_str):
            payment_cols.append(col_str)
        # Паттерн для YYYY
        elif re.match(r'^\d{4}$', col_str):
            payment_cols.append(col_str)
    return payment_cols
