# Generated by Django 5.1.2 on 2024-10-31 00:30

from django.db import migrations, models
from django.db.models import F


def copy_field(apps, schema):
    ActivityLog = apps.get_model('HeroHours', 'activitylog')
    ActivityLog.objects.all().update(entered=F('userID'))

class Migration(migrations.Migration):

    dependencies = [
        ('HeroHours', '0016_alter_users_total_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitylog',
            name='entered',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.RunPython(code=copy_field),
    ]
