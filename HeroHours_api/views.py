from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv_renderers

from HeroHours.models import Users
from HeroHours_api.authentication import URLTokenAuthentication


# Create your views here.
class TodoListApiView(APIView):
    renderer_classes = [csv_renderers.CSVRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        members = list(Users.objects.all().values())
        return Response(members, status=status.HTTP_200_OK)