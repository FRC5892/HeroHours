# Generated by Django 5.1.2 on 2024-10-14 20:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HeroHours', '0012_alter_activitylog_options_alter_users_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activitylog',
            options={'ordering': ['-timestamp']},
        ),
    ]
