import logging
import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from .analytics_views import get_developers_data

logger = logging.getLogger(__name__)


class DeveloperExportService:
    """
    Сервис для экспорта данных разработчиков в Excel.

    Предоставляет методы для экспорта:
    - Таблицы разработчиков
    - Аналитических метрик
    - Данных графика активности
    """

    @staticmethod
    def _format_excel_worksheet(worksheet):
        """
        Форматирует лист Excel.

        Применяет:
        - Цветное оформление заголовков
        - Автоматическую ширину столбцов
        - Выравнивание
        """
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")

        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception as e:
                    logger.debug('Пропуск ячейки при расчёте ширины столбца: %s', e)
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    @classmethod
    def export_table_to_excel(cls, filters=None):
        """
        Экспортирует таблицу разработчиков в Excel.
        """
        developers_data = get_developers_data(filters)

        if not developers_data:
            # Пустой DataFrame если нет данных
            df = pd.DataFrame(columns=['ФИО', 'Направление', 'Последняя активность', 'Количество интервью'])
        else:
            df = pd.DataFrame(developers_data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Разработчики', index=False)
            worksheet = writer.sheets['Разработчики']
            cls._format_excel_worksheet(worksheet)

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="developers_table.xlsx"'
        return response

    @classmethod
    def export_metrics_to_excel(cls):
        """
        Экспортирует аналитические метрики в Excel.

        Метрики:
        - Всего специалистов (активность за 15 дней)
        - Получили офферы (за текущий год)
        - Средний оффер (за последний месяц)
        - Топ направление по скорости
        - Топ направление по количеству офферов
        """
        from .analytics_views import get_developer_analytics_data
        data = get_developer_analytics_data()

        metrics_data = [
            {'Метрика': 'Всего специалистов', 'Значение': data.get('active-specialists', 0)},
            {'Метрика': 'Получили офферы (за текущий год)', 'Значение': data.get('offers-this-year', 0)},
            {'Метрика': 'Средний оффер (за последний месяц)', 'Значение': data.get('avg-offer-last-month', 0)},
            {'Метрика': 'Топ направление по скорости', 'Значение': data.get('fastest-direction', '—')},
            {'Метрика': 'Топ направлений по количеству офферов', 'Значение': data.get('top-direction-offers', '—')},
        ]

        df = pd.DataFrame(metrics_data)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Метрики', index=False)
            worksheet = writer.sheets['Метрики']
            cls._format_excel_worksheet(worksheet)

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="developers_metrics.xlsx"'
        return response

    @classmethod
    def export_chart_to_excel(cls):
        """
        Экспортирует данные графика активности в Excel.
        График показывает количество офферов за последние 12 месяцев.
        """
        from .analytics_views import get_developer_analytics_data
        data = get_developer_analytics_data()

        chart_data = data.get('chart_months', {})
        labels = chart_data.get('labels', [])
        values = chart_data.get('data', [])

        chart_df = pd.DataFrame({
            'Месяц': labels,
            'Количество офферов': values,
        })

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            chart_df.to_excel(writer, sheet_name='График активности', index=False)
            worksheet = writer.sheets['График активности']
            cls._format_excel_worksheet(worksheet)

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="developers_chart.xlsx"'
        return response
