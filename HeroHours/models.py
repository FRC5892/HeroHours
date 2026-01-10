"""
Django models for HeroHours attendance tracking system.

This module defines the database models for tracking user attendance,
check-in/check-out status, and activity logs.
"""
from django.db import models


class Users(models.Model):
    """
    Model representing a user/member in the HeroHours system.
    
    Tracks user information, check-in status, and total hours worked.
    """
    User_ID = models.IntegerField(primary_key=True)
    First_Name = models.CharField(max_length=50, db_index=True)  # Index for sorting
    Last_Name = models.CharField(max_length=50, db_index=True)   # Index for sorting
    Total_Hours = models.DurationField()
    Checked_In = models.BooleanField(default=False, db_index=True)  # Index for filtering
    Total_Seconds = models.FloatField(default=0)
    Last_In = models.DateTimeField(null=True, auto_now_add=True)
    Last_Out = models.DateTimeField(null=True)
    Is_Active = models.BooleanField(default=True, db_index=True)  # Index for filtering


    def get_total_hours(self):
        """
        Calculate and return a human-readable string of total hours worked.
        
        Returns:
            str: Formatted string like "5h 30m 45s"
            
        Performance:
            Uses integer division (divmod) for fast calculation
        """
        # Microoptimization: Cast once, use integer arithmetic
        total_secs = int(self.Total_Seconds)
        hours, remainder = divmod(total_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    class Meta:
        db_table = 'Users'
        verbose_name = "Member"
        verbose_name_plural = "Members"
        ordering = ['User_ID']
        # Microoptimization: Composite indexes for common queries
        indexes = [
            models.Index(fields=['Is_Active', 'Last_Name', 'First_Name']),  # For index view
            models.Index(fields=['Checked_In', 'Is_Active']),  # For checked_in count
        ]

    def __str__(self):
        return f"{self.First_Name} {self.Last_Name} ({self.User_ID})"


class ActivityLog(models.Model):
    """
    Model for logging all check-in/check-out activities.
    
    Maintains an audit trail of all attendance-related operations
    for reporting and debugging purposes.
    """
    OPERATION_CHOICES = [
        ('Check In', 'Check In'),
        ('Check Out', 'Check Out'),
        ('Reset', 'Reset'),
        ('None', 'None'),
    ]

    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Error', 'Error'),
        ('User Not Found', 'User Not Found'),
        ('Inactive User', 'Inactive User'),
        ('Invalid Input', 'Invalid Input'),
    ]

    user = models.ForeignKey(Users, models.CASCADE, blank=True, null=True, 
                            related_name='activity_logs')
    entered = models.TextField(help_text="The input value entered by the user")
    operation = models.CharField(max_length=20, choices=OPERATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    message = models.TextField(default='', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        # Microoptimization: Optimized indexes for common queries
        indexes = [
            models.Index(fields=['-timestamp']),  # For recent logs
            models.Index(fields=['user', '-timestamp']),  # For user-specific logs
            models.Index(fields=['status', '-timestamp']),  # For filtering by status
        ]
    
    def __str__(self):
        return f"{self.user_id} - {self.operation} - {self.status} - {self.timestamp}"