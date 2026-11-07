import logging

from django.core.cache import cache
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import extend_schema

from accounts.authentication import API_VIEW_AUTHENTICATION_CLASSES
from accounts.permissions import IsManagerOrAdmin
from core.decorators import ANALYTICS_CACHE_TIMEOUT, get_analytics_cache_key
from .analytics_views import compute_offer_analytics

logger = logging.getLogger('offers')

_CACHE_VIEW_NAME = 'offer_analytics_api'


class OfferAnalyticsAPIView(APIView):
    """
    Аналитика офферов для SPA.
    Ключ кэша совместим с legacy offer_analytics_api при пустых GET-параметрах.
    """

    authentication_classes = API_VIEW_AUTHENTICATION_CLASSES
    permission_classes = [IsManagerOrAdmin]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            raise NotAuthenticated()

    @extend_schema(
        summary='Аналитика по офферам',
        tags=['Аналитика'],
    )
    def get(self, request):
        params = request.query_params.dict()
        cache_key = get_analytics_cache_key(_CACHE_VIEW_NAME, params)

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        data = compute_offer_analytics()
        try:
            cache.set(cache_key, data, timeout=ANALYTICS_CACHE_TIMEOUT)
        except Exception as e:
            logger.warning('Не удалось записать кэш аналитики офферов: %s', e)

        return Response(data)
