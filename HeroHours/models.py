from django.db import models
from django.forms import model_to_dict


# Create your models here.
class Users(models.Model):
    User_ID = models.IntegerField(primary_key=True)
    First_Name = models.CharField(max_length=50)
    Last_Name = models.CharField(max_length=50)
    Total_Hours = models.DurationField()
    Checked_In = models.BooleanField(default=False)
    Total_Seconds = models.FloatField(default=0)
    Last_In = models.DateTimeField(null=True, auto_now_add=True)
    Last_Out = models.DateTimeField(null=True)
    Is_Active = models.BooleanField(default=True)


    def get_total_hours(self):
        hours, remainder = divmod(int(self.Total_Seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    class Meta:
        # Specify the table name
        db_table = 'Users'
        verbose_name = "Members"
        verbose_name_plural = "Members"

        def __str__(self):
            return f"{self.First_Name} {self.Last_Name}: {self.User_ID} - {self.Total_Hours}"


class ActivityLog(models.Model):
    OPERATION_CHOICES = [
        ('checkIn', 'Check In'),
        ('checkOut', 'Check Out'),
        ('none', "None"),
    ]

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('user not found', 'User Not Found'),
        ('inactive user', 'Inactive User'),
    ]

    user = models.ForeignKey(Users, models.CASCADE, blank=True, null=True)
    entered = models.TextField()
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(default='')  # Optional message field
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set the timestamp when creating

    def __str__(self):
        return f"{self.user_id} - {self.operation} - {self.status} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']  # Order by most recent logs first