"""
Management command to create superuser accounts from superusers.json file.
Users can add their credentials to superusers.json and they will be registered as administrators.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Creates superuser accounts from superusers.json configuration file'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Check if superusers.json exists
        config_file = 'superusers.json'
        if not os.path.exists(config_file):
            self.stdout.write(self.style.WARNING(f'{config_file} not found. No superusers to create.'))
            self.stdout.write(self.style.WARNING(f'   Create {config_file} with your superuser credentials to auto-register.'))
            return
        
        try:
            # Read the configuration file
            with open(config_file, 'r') as f:
                superusers_config = json.load(f)
            
            if not isinstance(superusers_config, list):
                self.stdout.write(self.style.ERROR(f'{config_file} must contain a JSON array of user objects'))
                return
            
            created_count = 0
            skipped_count = 0
            
            for user_data in superusers_config:
                username = user_data.get('username')
                email = user_data.get('email', '')
                password = user_data.get('password')
                first_name = user_data.get('first_name', '')
                last_name = user_data.get('last_name', '')
                
                if not username or not password:
                    self.stdout.write(self.style.ERROR(f'Skipping user: missing username or password'))
                    continue
                
                # Check if user already exists
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists, skipping.'))
                    skipped_count += 1
                    continue
                
                try:
                    # Create the superuser
                    user = User.objects.create_superuser(
                        username=username,
                        email=email,
                        password=password,
                        first_name=first_name,
                        last_name=last_name
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created superuser: {username}'))
                    if email:
                        self.stdout.write(self.style.SUCCESS(f'   Email: {email}'))
                    created_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Failed to create superuser "{username}": {e}'))
            
            # Summary
            if created_count > 0 or skipped_count > 0:
                self.stdout.write('')
                self.stdout.write(self.style.SUCCESS(f'Summary:'))
                if created_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'Created: {created_count} superuser(s)'))
                if skipped_count > 0:
                    self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count} (already exist)'))
                self.stdout.write(self.style.SUCCESS(f'\n You can now log in to /admin/ with your credentials'))
            else:
                self.stdout.write(self.style.WARNING('No new superusers were created.'))
                
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON in {config_file}: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading {config_file}: {e}'))