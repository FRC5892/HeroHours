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
class SheetPullRenderer(csv_renderers.CSVRenderer):
    header = ['User_ID','Last_Name','First_Name','Is_Active','Total_Hours','Checked_In','Last_In','Last_Out']
    labels = {
        'User_ID': 'Id',
        'Last_Name': 'Last Name',
        'First_Name': 'First Name',
        'Is_Active': 'Is Active',
        'Total_Hours': 'Hours',
        'Checked_In': 'Checked In',
        'Last_In': 'Last In',
        'Last_Out': 'Last Out',
    }
class SheetPullAPI(APIView):
    renderer_classes = [SheetPullRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        members = list(Users.objects.all().values())
        return Response(members, status=status.HTTP_200_OK)

class MeetingListRender(csv_renderers.CSVRenderer):
    header = ['user_id','user__Last_Name','user__First_Name']
    labels = {
        'user_id': 'Id',
        'user__Last_Name': 'Last Name',
        'user__First_Name': 'First Name',
    }
class MeetingPullAPI(APIView):
    renderer_classes = [MeetingListRender]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, day, month, year, *args, **kwargs):
        query = (ActivityLog.objects.all()
                 .filter(timestamp__day=str(day),timestamp__month=str(month),timestamp__year=str(year),operation='Check In')
                 ).values('user_id','user__First_Name','user__Last_Name')
        members = list(query)
        return Response(members, status=status.HTTP_200_OK)