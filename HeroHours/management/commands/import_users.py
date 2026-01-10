"""
Management command to import users from a CSV file.

Expected CSV format:
User_ID,First_Name,Last_Name,Total_Hours,Checked_In,Total_Seconds

Usage:
    python manage.py import_users path/to/users.csv
"""
import csv
from django.core.management.base import BaseCommand
from HeroHours.models import Users


class Command(BaseCommand):
    help = 'Import users from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='The CSV file to import')

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        
        try:
            with open(csv_file, newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                users = []
                
                for row in reader:
                    # Create a user instance and append it to the list
                    user = Users(
                        User_ID=int(row['User_ID']),
                        First_Name=row['First_Name'],
                        Last_Name=row['Last_Name'],
                        Total_Hours=row['Total_Hours'],
                        Checked_In=row['Checked_In'].upper() == 'TRUE',
                        Total_Seconds=float(row['Total_Seconds'])
                    )
                    users.append(user)
                
                # Bulk create users in the database
                Users.objects.bulk_create(users, ignore_conflicts=True)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully imported {len(users)} users')
                )
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {csv_file}')
            )
        except KeyError as e:
            self.stdout.write(
                self.style.ERROR(f'Missing required column: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing users: {str(e)}')
            )
