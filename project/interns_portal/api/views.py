import logging
import os
import uuid

from celery.result import AsyncResult
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsInternPortalStudent
from core.celery_task_status import celery_task_status_payload
from core.throttling import PortalUploadThrottle
from core.video_upload_validation import validate_video_magic_header, validate_video_upload_size
from core.constants import INTERVIEW_FORMAT_ONLINE
from interviews.models import Interview

from ..constants import ALLOWED_VIDEO_EXTENSIONS, INTERNS_PORTAL_HIDDEN_INTERVIEW_TYPES, MAX_VIDEO_SIZE
from ..serializers import InternPortalInterviewSerializer
from ..services import get_intern_for_portal_user
from ..tasks import upload_video_to_s3
from ..upload_logging import UPLOAD_SENTINEL, portal_upload_log, portal_user_label
from ..yandex_upload import build_video_object_filename

logger = logging.getLogger('interns_portal')

# TTL метки живости задачи загрузки видео: если воркер не подхватил задачу
# за это время — считаем её потерянной и сбрасываем слот.
_UPLOAD_ALIVE_TTL = 900  # 15 минут
_UPLOAD_ALIVE_PREFIX = 'portal_upload_alive'


def _upload_alive_key(task_id: str) -> str:
    return f'{_UPLOAD_ALIVE_PREFIX}:{task_id}'


def _clear_upload_slot(interview_id: int, reason: str) -> None:
    """Сбрасывает sentinel __uploading__ после ошибки до постановки Celery-задачи."""
    cleared = Interview.objects.filter(
        pk=interview_id,
        upload_task_id=UPLOAD_SENTINEL,
    ).update(upload_task_id='')
    if cleared:
        portal_upload_log('warning', 'slot_cleared', interview_id, reason=reason)


class InternPortalPageSizePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 50


class InternPortalInterviewListAPIView(APIView):
    """GET: пагинированный список собеседований текущего студента."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsInternPortalStudent]

    @extend_schema(
        summary='Список собеседований студента (портал)',
        parameters=[
            OpenApiParameter(name='page', type=int, location=OpenApiParameter.QUERY),
        ],
        tags=['Портал студента'],
    )
    def get(self, request):
        intern = get_intern_for_portal_user(request.user)
        if not intern:
            return Response({'results': [], 'count': 0, 'next': None, 'previous': None})

        qs = (
            Interview.objects.filter(intern=intern)
            .exclude(interview_type__in=INTERNS_PORTAL_HIDDEN_INTERVIEW_TYPES)
            .select_related('intern', 'direction', 'company')
            .order_by('-date', '-time')
        )
        paginator = InternPortalPageSizePagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        ser = InternPortalInterviewSerializer(page, many=True)
        return paginator.get_paginated_response(ser.data)


class InternPortalVideoUploadAPIView(APIView):
    """POST multipart: загрузка записи собеседования в S3 (Celery)."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsInternPortalStudent]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [PortalUploadThrottle]

    @extend_schema(
        summary='Загрузить видеозапись собеседования',
        tags=['Портал студента'],
    )
    def post(self, request, interview_id):
        intern = get_intern_for_portal_user(request.user)
        if not intern:
            return Response(
                {'error': 'Аккаунт не привязан к студенту. Обратитесь к менеджеру.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        video_file = request.FILES.get('video')
        ext = os.path.splitext(video_file.name)[1].lower() if video_file else ''
        size_mb = round(video_file.size / (1024 * 1024), 2) if video_file and video_file.size else 0
        portal_upload_log(
            'info',
            'request_start',
            interview_id,
            ext=ext or 'none',
            size_mb=size_mb,
            user=portal_user_label(request.user),
        )

        with transaction.atomic():
            interview = get_object_or_404(
                Interview.objects.select_for_update(of=('self',)).select_related('intern', 'direction', 'company').exclude(
                    interview_type__in=INTERNS_PORTAL_HIDDEN_INTERVIEW_TYPES,
                ),
                pk=interview_id,
                intern=intern,
            )

            if interview.upload_task_id == UPLOAD_SENTINEL:
                portal_upload_log('warning', 'conflict_409', interview_id, reason='sentinel_active')
                return Response(
                    {'error': 'Загрузка уже выполняется. Дождитесь завершения перед повторной отправкой.'},
                    status=status.HTTP_409_CONFLICT,
                )

            if interview.upload_task_id:
                existing = AsyncResult(interview.upload_task_id)
                if existing.state in ('PENDING', 'STARTED', 'PROGRESS'):
                    portal_upload_log(
                        'warning',
                        'conflict_409',
                        interview_id,
                        reason='celery_active',
                        task_id=interview.upload_task_id,
                    )
                    return Response(
                        {'error': 'Загрузка уже выполняется. Дождитесь завершения перед повторной отправкой.'},
                        status=status.HTTP_409_CONFLICT,
                    )

            if interview.interview_format != INTERVIEW_FORMAT_ONLINE:
                portal_upload_log('warning', 'validation_failed', interview_id, reason='not_online_format')
                return Response(
                    {'error': 'Загрузка записи доступна только для собеседований в формате «Онлайн».'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Interview.objects.filter(pk=interview_id).update(upload_task_id=UPLOAD_SENTINEL)
            portal_upload_log('info', 'slot_reserved', interview_id)

        if not video_file:
            _clear_upload_slot(interview_id, 'no_file')
            portal_upload_log('warning', 'validation_failed', interview_id, reason='no_file')
            return Response({'error': 'Файл не передан'}, status=status.HTTP_400_BAD_REQUEST)

        if ext not in ALLOWED_VIDEO_EXTENSIONS:
            _clear_upload_slot(interview_id, 'invalid_extension')
            portal_upload_log('warning', 'validation_failed', interview_id, reason='invalid_extension', ext=ext)
            return Response(
                {
                    'error': (
                        f'Недопустимый формат файла. Допустимы: {", ".join(ALLOWED_VIDEO_EXTENSIONS)}'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        size_err = validate_video_upload_size(video_file.size)
        if size_err:
            _clear_upload_slot(interview_id, 'size_unknown')
            portal_upload_log('warning', 'validation_failed', interview_id, reason='size_unknown')
            return Response({'error': size_err}, status=status.HTTP_400_BAD_REQUEST)
        if video_file.size > MAX_VIDEO_SIZE:
            _clear_upload_slot(interview_id, 'size_exceeded')
            portal_upload_log('warning', 'validation_failed', interview_id, reason='size_exceeded', size_mb=size_mb)
            return Response(
                {'error': 'Файл превышает максимально допустимый размер (10 ГБ)'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        header = video_file.read(16)
        video_file.seek(0)
        magic_err = validate_video_magic_header(header, ext)
        if magic_err:
            _clear_upload_slot(interview_id, 'magic_header')
            portal_upload_log('warning', 'validation_failed', interview_id, reason='magic_header')
            return Response({'error': magic_err}, status=status.HTTP_400_BAD_REQUEST)

        upload_dir = os.path.join(settings.PRIVATE_UPLOAD_ROOT, 'intern_uploads')
        os.makedirs(upload_dir, exist_ok=True)

        unique_name = f'{interview_id}_{uuid.uuid4().hex}{ext}'
        tmp_path = os.path.join(upload_dir, unique_name)

        try:
            with open(tmp_path, 'wb') as dst:
                for chunk in video_file.chunks():
                    dst.write(chunk)
        except OSError:
            logger.exception(
                '[PORTAL_UPLOAD] phase=tmp_save_failed interview_id=%s tmp_basename=%s',
                interview_id,
                unique_name,
            )
            _clear_upload_slot(interview_id, 'tmp_save_oserror')
            return Response(
                {'error': 'Ошибка сохранения файла на сервере'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        tmp_exists = os.path.isfile(tmp_path)
        saved_size_mb = round(os.path.getsize(tmp_path) / (1024 * 1024), 2) if tmp_exists else 0
        portal_upload_log(
            'info',
            'tmp_saved',
            interview_id,
            tmp_basename=unique_name,
            tmp_exists=tmp_exists,
            size_mb=saved_size_mb,
        )

        object_filename = build_video_object_filename(interview, ext)
        try:
            task = upload_video_to_s3.delay(interview_id, tmp_path, object_filename)
        except Exception:
            logger.exception(
                '[PORTAL_UPLOAD] phase=celery_dispatch_failed interview_id=%s tmp_basename=%s',
                interview_id,
                unique_name,
            )
            _clear_upload_slot(interview_id, 'celery_dispatch_failed')
            return Response(
                {'error': 'Не удалось поставить задачу загрузки. Попробуйте позже.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        Interview.objects.filter(pk=interview_id).update(upload_task_id=task.id)
        cache.set(_upload_alive_key(task.id), '1', timeout=_UPLOAD_ALIVE_TTL)
        portal_upload_log(
            'info',
            'celery_dispatched',
            interview_id,
            task_id=task.id,
            object_basename=os.path.basename(object_filename),
            user=portal_user_label(request.user),
        )

        return Response({'task_id': task.id})


class InternPortalUploadTaskStatusAPIView(APIView):
    """GET: прогресс Celery только для задачи, привязанной к собеседованию студента."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsInternPortalStudent]

    @extend_schema(
        summary='Статус задачи загрузки видео (портал)',
        tags=['Портал студента'],
    )
    def get(self, request, task_id):
        intern = get_intern_for_portal_user(request.user)
        if not intern:
            return Response(status=status.HTTP_404_NOT_FOUND)

        interview = Interview.objects.filter(
            intern=intern,
            upload_task_id=task_id,
        ).first()
        if not interview:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload = celery_task_status_payload(task_id)
        if payload.get('state') == 'FAILURE':
            portal_upload_log(
                'warning',
                'poll_failure',
                interview.pk,
                task_id=task_id,
                status=payload.get('status', '')[:200],
            )
            Interview.objects.filter(pk=interview.pk, upload_task_id=task_id).update(upload_task_id=None)

        if payload.get('state') == 'PENDING' and not cache.get(_upload_alive_key(task_id)):
            portal_upload_log(
                'warning',
                'poll_task_lost',
                interview.pk,
                task_id=task_id,
            )
            Interview.objects.filter(pk=interview.pk, upload_task_id=task_id).update(upload_task_id=None)
            return Response({
                'state': 'FAILURE',
                'status': 'Задача загрузки не была выполнена. Попробуйте снова.',
                'current': 0,
                'total': 100,
            })

        return Response(payload)
