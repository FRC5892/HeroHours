import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from HeroHours.models import Users, ActivityLog  # Replace 'Log' with your actual log model

class Command(BaseCommand):
    help = 'Generate a CSV file of user meeting attendance'
    def add_arguments(self, parser):
        parser.add_argument(
            '--outfile',
            type=str,
            default='user_meetings.csv',
            help='The name of the output CSV file',
            required=True
        )

    def handle(self, *args, **kwargs):
        # Get the output file name from arguments
        output_file = kwargs['outfile']

        # Fetch all users
        users = Users.objects.all()

        # Fetch all unique meeting dates (rounded to the day)
        meeting_dates = ActivityLog.objects.dates('timestamp', 'day')  # Replace 'timestamp' with your log's datetime field

        # Prepare the CSV header
        header = ['User ID', 'Last Name', 'First Name'] + [date.strftime('%Y-%m-%d') for date in meeting_dates]

        # Open the CSV file for writing
        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)

            # Iterate through each user
            for user in users:
                # Prepare the row for the user
                row = [user.User_ID, user.Last_Name, user.First_Name]  # Replace 'id' and 'name' with your user model fields

                # Check if the user has a log entry for each meeting date
                for date in meeting_dates:
                    has_checked_in = ActivityLog.objects.filter(
                        user=user,  # Replace 'user' with the foreign key field in your log model
                        timestamp__date=date  # Replace 'timestamp' with your log's datetime field
                    ).exists()
                    row.append('x' if has_checked_in else '')

                # Write the row to the CSV
                writer.writerow(row)

        self.stdout.write(self.style.SUCCESS(f'CSV file "{output_file}" generated successfully.'))