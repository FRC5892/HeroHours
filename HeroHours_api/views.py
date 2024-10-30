from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv_renderers

from HeroHours.models import Users, ActivityLog
from HeroHoursRemake import settings
from HeroHours_api.authentication import URLTokenAuthentication


# Create your views here.
class SheetPullAPI(APIView):
    renderer_classes = [csv_renderers.CSVRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        members = list(Users.objects.all().values())
        return Response(members, status=status.HTTP_200_OK)

class MeetingPullAPI(APIView):
    renderer_classes = [csv_renderers.CSVRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, day, month, year, *args, **kwargs):
        query = (ActivityLog.objects.all()
                 .exclude(operation='None')
                 .filter(timestamp__day=day,timestamp__month=month,timestamp__year=year)
                 )
        print(f'JOIN {Users._meta.db_table} ON {ActivityLog._meta.db_table}.userID = {Users._meta.db_table}.User_ID')
        members = list(query)
        return Response(members, status=status.HTTP_200_OK)