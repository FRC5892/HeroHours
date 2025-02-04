import csv
import datetime
from django.core.management.base import BaseCommand
from HeroHours.models import Users
from HeroHours.views import handle_bulk_updates  # Replace 'yourapp' with your actual app name

class Command(BaseCommand):
    help = 'Run a comand at a specific time'

    def add_arguments(self, parser):
       parser.add_argument('userID', type=str, help='The userID/Command to run')
       parser.add_argument('time', type=str, help='The time to use')

    def handle(self, *args, **options):
        userID = options["userID"]
        time_string = options["time"].split()
        year = time_string[0]
        month = time_string[1]
        day = time_string[2]
        hour = time_string[3]
        minute = time_string[4]
        handle_bulk_updates(user_id=userID,time=datetime(year,month,day,hour,minute))
    