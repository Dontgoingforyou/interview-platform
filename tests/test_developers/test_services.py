"""
Тесты для services приложения developers.

Используются маркеры pytest:
- @pytest.mark.django_db - для работы с БД
- @pytest.mark.services - для группировки тестов сервисов
"""
import pytest
from datetime import date, timedelta
from io import BytesIO
from openpyxl import load_workbook

from developers.services import DeveloperExportService
from interviews.models import Interview
from offers.models import Offer


@pytest.mark.django_db(databases=['default'])
@pytest.mark.services
class TestDeveloperExportService:
    """Тесты для DeveloperExportService."""

    def test_export_table_to_excel_basic(
        self,
        intern,
        direction,
        offer
    ):
        """Базовый тест экспорта таблицы в Excel."""
        response = DeveloperExportService.export_table_to_excel()

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'developers_table.xlsx' in response['Content-Disposition']

    def test_export_table_to_excel_content(
        self,
        intern,
        direction,
        offer
    ):
        """Проверка содержимого экспортированного файла."""
        response = DeveloperExportService.export_table_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем заголовки
        headers = [cell.value for cell in worksheet[1]]
        assert 'ФИО' in headers
        assert 'Направление' in headers
        assert 'Последняя активность' in headers
        assert 'Количество интервью' in headers

    def test_export_table_to_excel_with_data(
        self,
        intern,
        direction,
        manager,
        offer
    ):
        """Экспорт таблицы с данными."""
        today = date.today()

        # Создаём интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        response = DeveloperExportService.export_table_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем, что есть данные (заголовок + минимум 1 строка)
        assert worksheet.max_row >= 2

    def test_export_table_to_excel_empty(self):
        """Экспорт пустой таблицы."""
        response = DeveloperExportService.export_table_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Должен быть только заголовок
        assert worksheet.max_row == 1

    def test_export_table_to_excel_with_filters(
        self,
        intern,
        direction,
        offer
    ):
        """Экспорт таблицы с фильтрами."""
        filters = {
            'direction': direction.id,
            'q': 'Иван',
            'order_by': 'full_name',
            'order_dir': 'asc'
        }

        response = DeveloperExportService.export_table_to_excel(filters)

        assert response.status_code == 200

    def test_export_table_to_excel_formatting(
        self,
        intern,
        direction,
        offer
    ):
        """Проверка форматирования Excel файла."""
        response = DeveloperExportService.export_table_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем форматирование заголовков
        first_cell = worksheet['A1']
        assert first_cell.fill.start_color.rgb == '00366092'  # Цвет заголовка
        assert first_cell.font.bold is True
        # Цвет может быть с префиксом '00' или без
        assert first_cell.font.color.rgb in ['FFFFFFFF', '00FFFFFF']  # Белый цвет текста

    def test_export_metrics_to_excel_basic(self):
        """Базовый тест экспорта метрик в Excel."""
        response = DeveloperExportService.export_metrics_to_excel()

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'developers_metrics.xlsx' in response['Content-Disposition']

    def test_export_metrics_to_excel_content(self):
        """Проверка содержимого метрик."""
        response = DeveloperExportService.export_metrics_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем заголовки
        headers = [cell.value for cell in worksheet[1]]
        assert 'Метрика' in headers
        assert 'Значение' in headers

    def test_export_metrics_to_excel_metrics_list(self):
        """Проверка списка метрик."""
        response = DeveloperExportService.export_metrics_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Получаем все метрики из первого столбца (пропускаем заголовок)
        metrics = [worksheet.cell(row=i, column=1).value for i in range(2, worksheet.max_row + 1)]

        assert 'Всего специалистов' in metrics
        assert 'Получили офферы (за текущий год)' in metrics
        assert 'Средний оффер (за последний месяц)' in metrics
        assert 'Топ направление по скорости' in metrics
        assert 'Топ направлений по количеству офферов' in metrics

    def test_export_metrics_to_excel_with_data(
        self,
        intern,
        direction,
        manager,
        offer_this_year
    ):
        """Экспорт метрик с реальными данными."""
        today = date.today()

        # Создаём интервью
        Interview.objects.create(
            intern=intern,
            direction=direction,
            manager_email=manager.email,
            interview_type='screening',
            date=today - timedelta(days=5)
        )

        response = DeveloperExportService.export_metrics_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем, что метрики не нулевые
        # Находим строку с "Получили офферы (за текущий год)"
        for i in range(2, worksheet.max_row + 1):
            if worksheet.cell(row=i, column=1).value == 'Получили офферы (за текущий год)':
                value = worksheet.cell(row=i, column=2).value
                assert value >= 1
                break

    def test_export_metrics_to_excel_formatting(self):
        """Проверка форматирования метрик."""
        response = DeveloperExportService.export_metrics_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем форматирование заголовков
        first_cell = worksheet['A1']
        assert first_cell.fill.start_color.rgb == '00366092'
        assert first_cell.font.bold is True

    def test_export_chart_to_excel_basic(self):
        """Базовый тест экспорта графика в Excel."""
        response = DeveloperExportService.export_chart_to_excel()

        assert response.status_code == 200
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'developers_chart.xlsx' in response['Content-Disposition']

    def test_export_chart_to_excel_content(self):
        """Проверка содержимого графика."""
        response = DeveloperExportService.export_chart_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем заголовки
        headers = [cell.value for cell in worksheet[1]]
        assert 'Месяц' in headers
        assert 'Количество офферов' in headers

    def test_export_chart_to_excel_with_data(
        self,
        intern,
        direction
    ):
        """Экспорт графика с данными."""
        today = date.today()

        # Создаём офферы для текущего месяца
        Offer.objects.create(
            intern=intern,
            direction=direction,
            company='Google',
            amount=150000,
            month=today.month,
            year=today.year
        )

        response = DeveloperExportService.export_chart_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем, что есть данные (заголовок + строки с данными)
        assert worksheet.max_row >= 2

    def test_export_chart_to_excel_empty(self):
        """Экспорт пустого графика."""
        response = DeveloperExportService.export_chart_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Должен быть только заголовок (данных нет)
        assert worksheet.max_row == 1

    def test_export_chart_to_excel_formatting(self):
        """Проверка форматирования графика."""
        response = DeveloperExportService.export_chart_to_excel()

        # Загружаем Excel файл
        excel_file = BytesIO(response.content)
        workbook = load_workbook(excel_file)
        worksheet = workbook.active

        # Проверяем форматирование заголовков
        first_cell = worksheet['A1']
        assert first_cell.fill.start_color.rgb == '00366092'
        assert first_cell.font.bold is True

    def test_format_excel_worksheet(self):
        """Тест метода форматирования worksheet."""
        from openpyxl import Workbook

        # Создаём тестовый workbook
        wb = Workbook()
        ws = wb.active

        # Добавляем данные
        ws.append(['Заголовок 1', 'Заголовок 2', 'Заголовок 3'])
        ws.append(['Данные 1', 'Данные 2', 'Данные 3'])

        # Применяем форматирование
        DeveloperExportService._format_excel_worksheet(ws)

        # Проверяем, что заголовки отформатированы
        assert ws['A1'].fill.start_color.rgb == '00366092'
        assert ws['A1'].font.bold is True
        # Цвет может быть с префиксом '00' или без
        assert ws['A1'].font.color.rgb in ['FFFFFFFF', '00FFFFFF']

        # Проверяем, что ширина столбцов установлена
        assert ws.column_dimensions['A'].width > 0

    def test_column_width_adjustment(self):
        """Тест автоматической настройки ширины столбцов."""
        from openpyxl import Workbook

        # Создаём тестовый workbook с длинным текстом
        wb = Workbook()
        ws = wb.active

        ws.append(['Короткий', 'Очень длинный заголовок столбца'])
        ws.append(['A', 'B'])

        # Применяем форматирование
        DeveloperExportService._format_excel_worksheet(ws)

        # Проверяем, что ширина второго столбца больше первого
        assert ws.column_dimensions['B'].width > ws.column_dimensions['A'].width

    def test_column_width_max_limit(self):
        """Тест максимального ограничения ширины столбца."""
        from openpyxl import Workbook

        # Создаём тестовый workbook с очень длинным текстом
        wb = Workbook()
        ws = wb.active

        very_long_text = 'A' * 100  # 100 символов
        ws.append([very_long_text])

        # Применяем форматирование
        DeveloperExportService._format_excel_worksheet(ws)

        # Проверяем, что ширина не превышает максимум (50)
        assert ws.column_dimensions['A'].width <= 50

    def test_multiple_exports_independence(
        self,
        intern,
        direction,
        offer
    ):
        """Проверка независимости множественных экспортов."""
        # Экспортируем таблицу
        response1 = DeveloperExportService.export_table_to_excel()

        # Экспортируем метрики
        response2 = DeveloperExportService.export_metrics_to_excel()

        # Экспортируем график
        response3 = DeveloperExportService.export_chart_to_excel()

        # Все экспорты должны быть успешными
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        # Все должны иметь разные имена файлов
        assert 'table' in response1['Content-Disposition']
        assert 'metrics' in response2['Content-Disposition']
        assert 'chart' in response3['Content-Disposition']
