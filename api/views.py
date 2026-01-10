from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework.views import APIView
from rest_framework.settings import api_settings
from rest_framework_csv import renderers as csv_renderers
from django.db.models import Subquery
from HeroHours.models import Users, ActivityLog
from config import settings
from api.authentication import URLTokenAuthentication


# Create your views here.
class SheetPullRenderer(csv_renderers.CSVRenderer):
    header = ['Id','Last Name','First Name','Is Active','Hours','Checked In','Last In','Last Out']
class SheetPullAPI(APIView):
    renderer_classes = [SheetPullRenderer]
    authentication_classes = [URLTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        members = Users.objects.all().order_by('Last_Name','First_Name')
        content = [{
                    'Id': member.User_ID,
                    'Last Name': member.Last_Name,
                    'First Name': member.First_Name,
                    'Is Active': member.Is_Active,
                    'Hours': member.get_total_hours(),
                    'Checked In': member.Checked_In,
                    'Last In': member.Last_In,
                    'Last Out': member.Last_Out,
                    } for member in members]
        return Response(content, status=status.HTTP_200_OK)

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
        query = ActivityLog.objects.filter(id__in=Subquery(
            ActivityLog.objects.all()
            .filter(timestamp__day=str(day),timestamp__month=str(month),timestamp__year=str(year),operation='Check In') \
                .order_by('user_id').distinct('user_id').values('id')
        )).order_by('user__Last_Name','user__First_Name').values('user_id','user__First_Name','user__Last_Name')
        members = list(query)

        return Response(members, status=status.HTTP_200_OK)