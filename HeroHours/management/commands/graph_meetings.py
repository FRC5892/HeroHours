"""
Management command to generate a CSV file of user meeting attendance.
This command creates a CSV matrix showing which users attended on which dates.
Rows represent users, columns represent unique meeting dates, and 'x' marks
indicate attendance on that date.
Usage:
    python manage.py graph_meetings --outfile user_meetings.csv
"""
import csv
from typing import Any
from django.core.management.base import BaseCommand
from HeroHours.models import Users, ActivityLog


class Command(BaseCommand):
    help = 'Generate a CSV file of user meeting attendance'

    def add_arguments(self, parser) -> None:
        """
        Configure command line arguments.
        
        Args:
            parser: ArgumentParser instance for adding command arguments
        """
        parser.add_argument(
            '--outfile',
            type=str,
            default='user_meetings.csv',
            help='The name of the output CSV file',
            required=True
        )

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Generate CSV file with user meeting attendance data.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments including 'outfile'
        """
        output_file = kwargs['outfile']

        try:
            # Fetch all users - only the fields we need for performance
            users = Users.objects.only('User_ID', 'Last_Name', 'First_Name').order_by('User_ID')

            # Fetch all unique meeting dates (rounded to the day)
            meeting_dates = ActivityLog.objects.dates('timestamp', 'day').order_by('timestamp')

            # Prepare the CSV header
            header = ['User ID', 'Last Name', 'First Name'] + [
                date.strftime('%Y-%m-%d') for date in meeting_dates
            ]

            # Open the CSV file for writing
            with open(output_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(header)

                # Iterate through each user
                for user in users:
                    # Prepare the row for the user
                    row = [user.User_ID, user.Last_Name, user.First_Name]

                    # Check if the user has a log entry for each meeting date
                    for date in meeting_dates:
                        has_checked_in = ActivityLog.objects.filter(
                            user=user,
                            timestamp__date=date
                        ).exists()
                        row.append('x' if has_checked_in else '')

                    # Write the row to the CSV
                    writer.writerow(row)

            self.stdout.write(
                self.style.SUCCESS(f'CSV file "{output_file}" generated successfully.')
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'Unable to create file: {output_file}')
            )
        except PermissionError:
            self.stdout.write(
                self.style.ERROR(f'Permission denied to write file: {output_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating CSV file: {str(e)}')
            )