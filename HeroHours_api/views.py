from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv_renderers

from HeroHours.models import Users
from HeroHours_api.serializers import TodoSerializer


# Create your views here.
class TodoListApiView(APIView):
    renderer_classes = (csv_renderers.CSVRenderer,) + tuple(api_settings.DEFAULT_RENDERER_CLASSES)
    @renderer_classes((TodoSerializer))
    def get(self, request, *args, **kwargs):
        members = Users.objects.all()
        return Response(serializer.render(data=members), status=status.HTTP_200_OK)