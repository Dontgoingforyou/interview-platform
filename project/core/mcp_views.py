"""HTTP MCP endpoint."""
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import KeycloakSessionAuthentication
from accounts.permissions import IsManagerOrAdmin
from core.http_mcp import handle_mcp_request
from drf_spectacular.utils import extend_schema


class HttpMcpView(APIView):
    """
    JSON-RPC MCP: initialize, tools/list, tools/call.

    MCP доступен по пути /mcp для сессии локального входа.
    """

    authentication_classes = [KeycloakSessionAuthentication]
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    parser_classes = [JSONParser]
    http_method_names = ['post', 'head', 'options']

    @extend_schema(
        summary='HTTP MCP',
        description=(
            'JSON-RPC 2.0: initialize, tools/list, tools/call. '
            'Авторизация: сессия локального входа.'
        ),
        tags=['MCP'],
        request={'application/json': {'type': 'object'}},
        responses={200: {'description': 'JSON-RPC result или error'}},
    )
    def post(self, request):
        return Response(handle_mcp_request(request, request.data))
