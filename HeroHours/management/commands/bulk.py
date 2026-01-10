"""
Management command to run bulk operations at a specific time.

Usage:
    python manage.py bulk <userID/Command> "<year month day hour minute>"
"""
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from HeroHours.models import Users
from HeroHours.views import _handle_bulk_updates


class Command(BaseCommand):
    help = 'Run a bulk command at a specific time'

    def add_arguments(self, parser):
        parser.add_argument('userID', type=str, help='The userID/Command to run')
        parser.add_argument('time', type=str, help='The time to use (format: YYYY MM DD HH MM)')

    def handle(self, *args, **options):
        user_id = options["userID"]
        time_string = options["time"].split()
        
        if len(time_string) != 5:
            self.stdout.write(self.style.ERROR(
                'Time format must be: YYYY MM DD HH MM'
            ))
            return
        
        try:
            year, month, day, hour, minute = map(int, time_string)
            target_time = datetime(year, month, day, hour, minute)
            
            _handle_bulk_updates(user_id=user_id, time=target_time)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully executed bulk command for {user_id} at {target_time}'
            ))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(
                f'Invalid time format: {str(e)}'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error executing command: {str(e)}'
            ))

    