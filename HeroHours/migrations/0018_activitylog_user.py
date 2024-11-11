# Generated by Django 5.1.2 on 2024-10-31 00:33

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F


def copy_field(apps, schema):
    ActivityLog = apps.get_model('HeroHours', 'activitylog')
    Users = apps.get_model('HeroHours', 'users')
    updated_log = []
    for log in ActivityLog.objects.all().iterator():
        if Users.objects.filter(User_ID=log.userID).exists():
            log.user_id = log.userID
            updated_log.append(log)
    ActivityLog.objects.bulk_update(updated_log, ["user"])


class Migration(migrations.Migration):

    dependencies = [
        ('HeroHours', '0017_activitylog_entered'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitylog',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='HeroHours.users'),
        ),
        migrations.RunPython(code=copy_field),
        migrations.RemoveField(
            model_name='activitylog',
            name='userID',
        ),
    ]
