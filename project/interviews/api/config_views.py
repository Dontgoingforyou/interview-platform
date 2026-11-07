"""Вспомогательные эндпоинты для React SPA (Deepgram)."""
import logging

from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsAdminRole
from transcriptions.services import TranscriptionService

logger = logging.getLogger('interviews')


class DeepgramBalanceAPIView(APIView):
    """Баланс Deepgram для админ-панели списка собеседований."""

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsAdminRole]

    @extend_schema(
        summary='Баланс Deepgram',
        description='Только администратор.',
        tags=['Интервью'],
    )
    def get(self, request):
        try:
            balance = TranscriptionService.get_balance()
            return Response(balance)
        except Exception as e:
            logger.warning('Deepgram balance: %s', e)
            return Response({'amount': None, 'error': str(e)})
