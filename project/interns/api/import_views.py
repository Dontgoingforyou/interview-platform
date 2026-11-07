import logging

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole
from core.constants import INTERN_IMPORT_COLUMN_MAPPING
from core.import_tasks import async_import_from_file, register_import_task_owner
from core.import_upload import save_import_upload_file, validate_import_filename
from interns.services import InternImportService, InternSyncImportService, RealInterviewDateImportService

logger = logging.getLogger('interns.import_api')


class InternImportAPIView(APIView):
    """POST multipart: полный импорт студентов (только admin)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary='Импорт студентов из файла',
        description='Загрузка CSV/XLSX, постановка Celery-задачи. Только администратор.',
        tags=['Студенты'],
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

        tmp_path, err = save_import_upload_file(uploaded_file, 'interns')
        if err:
            logger.exception('Ошибка сохранения файла импорта студентов')
            return Response({'status': 'error', 'message': err}, status=500)

        task_params = {
            'file_path': tmp_path,
            'service_class_path': f'{InternImportService.__module__}.{InternImportService.__name__}',
            'column_mapping': INTERN_IMPORT_COLUMN_MAPPING,
            'required_columns': ['full_name'],
        }
        try:
            task = async_import_from_file.delay(**task_params)
        except Exception as e:
            logger.exception('Ошибка запуска Celery-задачи импорта студентов: %s', e)
            return Response({'status': 'error', 'message': f'Ошибка запуска задачи: {e!s}'}, status=500)

        register_import_task_owner(task.id, request.user.email)
        return Response({'status': 'started', 'task_id': task.id})


class InternSyncImportAPIView(APIView):
    """POST multipart: синхронизация студентов из файла (merge-only, только admin)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary='Синхронизация студентов из файла',
        description=(
            'Загрузка CSV/XLSX, постановка Celery-задачи. '
            'Дополняет пустые поля, не затирает заполненные. Только администратор.'
        ),
        tags=['Студенты'],
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

        tmp_path, err = save_import_upload_file(uploaded_file, 'interns_sync')
        if err:
            logger.exception('Ошибка сохранения файла синхронизации студентов')
            return Response({'status': 'error', 'message': err}, status=500)

        task_params = {
            'file_path': tmp_path,
            'service_class_path': (
                f'{InternSyncImportService.__module__}.{InternSyncImportService.__name__}'
            ),
            'column_mapping': INTERN_IMPORT_COLUMN_MAPPING,
            'required_columns': ['full_name'],
        }
        try:
            task = async_import_from_file.delay(**task_params)
        except Exception as e:
            logger.exception('Ошибка запуска Celery-задачи синхронизации студентов: %s', e)
            return Response({'status': 'error', 'message': f'Ошибка запуска задачи: {e!s}'}, status=500)

        register_import_task_owner(task.id, request.user.email)
        return Response({'status': 'started', 'task_id': task.id})


class InternImportDatesAPIView(APIView):
    """POST multipart: импорт дат реальных собеседований (только admin)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary='Импорт дат реальных собеседований',
        description='Обновление поля real_interview_date по файлу с колонками «ФИ» и «Дата».',
        tags=['Студенты'],
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

        tmp_path, err = save_import_upload_file(uploaded_file, 'intern_dates')
        if err:
            logger.exception('Ошибка сохранения файла импорта дат')
            return Response({'status': 'error', 'message': err}, status=500)

        task_params = {
            'file_path': tmp_path,
            'service_class_path': (
                f'{RealInterviewDateImportService.__module__}.{RealInterviewDateImportService.__name__}'
            ),
            'column_mapping': None,
            'required_columns': ['ФИ', 'Дата'],
        }
        try:
            task = async_import_from_file.delay(**task_params)
        except Exception as e:
            logger.exception('Ошибка запуска Celery-задачи импорта дат: %s', e)
            return Response({'status': 'error', 'message': f'Ошибка запуска задачи: {e!s}'}, status=500)

        register_import_task_owner(task.id, request.user.email)
        return Response({'status': 'started', 'task_id': task.id})
