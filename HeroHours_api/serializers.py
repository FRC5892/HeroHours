from rest_framework import serializers
from rest_framework_csv.renderers import CSVRenderer

from HeroHours.models import Users


class TodoSerializer(CSVRenderer):
    class Meta:
        model = Users
        fields = ["User_ID","First_Name","Last_Name","Total_Hours","Total_Seconds","Last_In","Last_Out","Is_Active"]


