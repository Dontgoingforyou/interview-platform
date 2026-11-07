import logging

from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole
from core.import_tasks import async_import_from_file, register_import_task_owner
from core.import_upload import save_import_upload_file, validate_import_filename

from ..import_excel_config import COLUMN_MAPPING, REQUIRED_COLUMNS
from ..services import OfferImportService

logger = logging.getLogger('offers_import')


class OfferImportAPIView(APIView):
    """POST multipart: CSV/XLSX — асинхронный импорт офферов (только admin)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary='Импорт офферов из файла',
        description='Загрузка CSV/XLSX, постановка Celery-задачи. Только администратор.',
        tags=['Офферы'],
    )
    def post(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'status': 'error', 'message': 'Файл не выбран.'}, status=400)

        if not validate_import_filename(uploaded_file.name):
            return Response(
                {
                    'status': 'error',
                    'message': 'Неподдерживаемый формат файла. Пожалуйста, загрузите CSV или XLSX.',
                },
                status=400,
            )

        tmp_path, err = save_import_upload_file(uploaded_file, 'offers')
        if err:
            logger.exception('Ошибка сохранения файла импорта офферов')
            return Response({'status': 'error', 'message': err}, status=500)

        task_params = {
            'file_path': tmp_path,
            'service_class_path': f'{OfferImportService.__module__}.{OfferImportService.__name__}',
            'column_mapping': COLUMN_MAPPING,
            'required_columns': REQUIRED_COLUMNS,
        }
        try:
            task = async_import_from_file.delay(**task_params)
        except Exception as e:
            logger.exception('Ошибка запуска Celery-задачи импорта офферов: %s', e)
            return Response({'status': 'error', 'message': f'Ошибка запуска задачи: {e!s}'}, status=500)

        register_import_task_owner(task.id, request.user.email)
        return Response({'status': 'started', 'task_id': task.id})
