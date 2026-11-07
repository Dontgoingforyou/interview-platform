import logging

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole, IsManagerOrAdmin
from core.celery_task_status import celery_task_status_payload
from core.constants import INTERVIEW_COLUMN_MAPPING
from core.import_tasks import async_import_from_file, register_import_task_owner
from core.import_upload import save_import_upload_file, validate_import_filename
from interviews.services import InterviewImportService

logger = logging.getLogger('interview_import')


class InterviewImportAPIView(APIView):
    """POST multipart: файл CSV/XLSX — запуск асинхронного импорта (только admin)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary='Импорт собеседований из файла',
        description='Загрузка CSV/XLSX, постановка Celery-задачи. Только администратор.',
        tags=['Интервью'],
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

        tmp_path, err = save_import_upload_file(uploaded_file, 'interviews')
        if err:
            logger.exception('Ошибка сохранения файла импорта')
            return Response({'status': 'error', 'message': err}, status=500)

        task_params = {
            'file_path': tmp_path,
            'service_class_path': f'{InterviewImportService.__module__}.{InterviewImportService.__name__}',
            'column_mapping': INTERVIEW_COLUMN_MAPPING,
            'required_columns': [
                'full_name',
                'direction_name',
                'interview_type_label',
                'date_str',
                'manager_name',
            ],
        }
        try:
            task = async_import_from_file.delay(**task_params)
        except Exception as e:
            logger.exception('Ошибка запуска Celery-задачи импорта: %s', e)
            return Response({'status': 'error', 'message': f'Ошибка запуска задачи: {e!s}'}, status=500)

        register_import_task_owner(task.id, request.user.email)
        return Response({'status': 'started', 'task_id': task.id})


class ImportTaskStatusAPIView(APIView):
    """Статус Celery-задачи импорта (для SPA с Bearer)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    @extend_schema(
        summary='Статус задачи импорта',
        description='Прогресс асинхронного импорта по task_id.',
        tags=['Интервью'],
    )
    def get(self, request, task_id):
        return Response(celery_task_status_payload(task_id))
