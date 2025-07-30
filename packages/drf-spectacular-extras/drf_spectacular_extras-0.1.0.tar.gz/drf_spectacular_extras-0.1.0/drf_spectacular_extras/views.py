import json

from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.views import APIView

from drf_spectacular.plumbing import get_relative_url, set_query_parameters
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import extend_schema

from .settings import spectacular_extras_settings

if spectacular_settings.SERVE_AUTHENTICATION is not None:
    AUTHENTICATION_CLASSES = spectacular_settings.SERVE_AUTHENTICATION
else:  # pragma: no cover
    AUTHENTICATION_CLASSES = api_settings.DEFAULT_AUTHENTICATION_CLASSES


class SpectacularScalarView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    permission_classes = spectacular_settings.SERVE_PERMISSIONS
    authentication_classes = AUTHENTICATION_CLASSES
    url_name: str = "schema"
    url: str | None = None
    template_name: str = "drf_spectacular/scalar.html"
    title: str | None = spectacular_settings.TITLE

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        return Response(
            data={
                "title": self.title,
                "scalar_standalone": self._scalar_standalone(),
                "schema_url": self._get_schema_url(request),
                "settings": self._dump(spectacular_extras_settings.SCALAR_UI_SETTINGS),
            },
            template_name=self.template_name,
        )

    def _dump(self, data):
        data = data or {}
        return json.dumps(data, indent=2)

    @staticmethod
    def _scalar_standalone():
        return f"{spectacular_extras_settings.SCALAR_DIST}/dist/browser/standalone.js"

    def _get_schema_url(self, request):
        schema_url = self.url or get_relative_url(
            reverse(self.url_name, request=request)
        )
        return set_query_parameters(
            url=schema_url,
            lang=request.GET.get("lang"),
            version=request.GET.get("version"),
        )
