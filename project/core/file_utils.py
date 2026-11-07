import logging
import pandas as pd
from io import BytesIO

logger = logging.getLogger(__name__)


def read_file_content(uploaded_file, max_size_mb=100):
    """
    Читает содержимое файла и возвращает DataFrame.

    Args:
        uploaded_file: Загруженный файл
        max_size_mb: Максимальный размер файла в МБ (по умолчанию 100)

    Raises:
        ValueError: Если файл слишком большой или неподдерживаемый формат
    """
    try:
        # Проверка размера файла перед чтением
        file_size = uploaded_file.size
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            error_msg = (
                f"Файл слишком большой: {file_size / (1024 * 1024):.2f} МБ. "
                f"Максимальный размер: {max_size_mb} МБ."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        file_content = uploaded_file.read()
        filename = uploaded_file.name.lower()

        if filename.endswith('.csv'):
            read_csv_kwargs = {
                'encoding': 'utf-8-sig',
                'engine': 'python',
            }
            try:
                df = pd.read_csv(
                    BytesIO(file_content),
                    on_bad_lines='warn',
                    **read_csv_kwargs,
                )
            except TypeError:
                df = pd.read_csv(BytesIO(file_content), **read_csv_kwargs)
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
        else:
            raise ValueError(
                f"Неподдерживаемый формат файла: {filename}"
            )

        file_info = f"Файл '{uploaded_file.name}' прочитан. Строк: {len(df)}, Размер: {file_size / (1024 * 1024):.2f} МБ"
        logger.info(file_info)
        return df
    except pd.errors.EmptyDataError:
        logger.error("Файл оказался пустым.")
        raise
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise


def rename_columns(df, column_mapping):
    """ Переименовывает столбцы в DataFrame по заданному словарю. """
    rename_dict = {
        k: v for k, v in column_mapping.items() if k in df.columns
    }
    df = df.rename(columns=rename_dict)
    old_names = list(rename_dict.keys())
    new_names = list(rename_dict.values())
    logger.info(f"Столбцы переименованы: {old_names} -> {new_names}")
    return df


def validate_required_columns(df, required_columns, column_mapping=None):
    """ Проверяет наличие обязательных столбцов в DataFrame. """
    if column_mapping is None:
        # Простая проверка без маппинга
        missing_columns = [
            col for col in required_columns if col not in df.columns
        ]
        if missing_columns:
            logger.error(
                f"Отсутствуют обязательные столбцы: {missing_columns}"
            )
            return False, missing_columns
        return True, []
    else:
        # Проверка с учетом маппинга
        missing_headers = []
        for req_key in required_columns:
            # Находим оригинальный заголовок в файле
            original_header = None
            for k, v in column_mapping.items():
                if v == req_key and k in df.columns:
                    original_header = k
                    break
            if not original_header:
                missing_headers.append(req_key)

        if missing_headers:
            # Находим оригинальные названия столбцов
            original_missing = [
                k for k in column_mapping.keys()
                if (column_mapping[k] in missing_headers
                    and k not in df.columns)
            ]
            logger.error(
                f"Отсутствуют обязательные столбцы: {original_missing}"
            )
            return False, original_missing
        return True, []


def truncate_string(value, max_length, default=''):
    """ Обрезает строку до заданной длины. """
    if pd.isna(value):
        return default
    value = str(value)
    return value[:max_length] if value else default


def clean_field(value, default=''):
    """ Приводит поле к нормальному виду (заменяет 'nan' на пустую). """
    if pd.isna(value) or value == 'nan':
        return default
    return str(value).strip()
