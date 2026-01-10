"""
Django Admin Configuration for HeroHours Application

This module configures the Django admin interface for managing Users and ActivityLog models.
Includes custom actions for bulk check-in/check-out operations and user management.
"""
import csv
import json
import logging
from datetime import datetime
from types import SimpleNamespace

import django.contrib.auth.models as authModels
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.admin.utils import unquote
from rest_framework.authtoken.admin import TokenAdmin

from HeroHours.forms import CustomActionForm
from . import models
from .models import Users, ActivityLog

logger = logging.getLogger(__name__)

# Configure TokenAdmin to use raw_id_fields for better performance
TokenAdmin.raw_id_fields = ['user']


@admin.action(description="Check Out Members")
def check_out(modeladmin, request, queryset):
    """
    Admin action to check out selected users.
    
    Calculates total hours worked and updates user records atomically.
    """
    with transaction.atomic():
        checked_in_users = queryset.select_for_update().filter(Checked_In=True)
        updated_users = []
        updated_logs = []
        
        for user in checked_in_users:
            if user.Last_In:
                # Calculate time worked
                time_delta = (timezone.now() - user.Last_In).total_seconds()
                user.Total_Seconds += round(time_delta)
                user.Total_Hours = (
                    datetime.combine(datetime.today(), user.Total_Hours) + 
                    (timezone.now() - user.Last_In)
                ).time()
            
            user.Checked_In = False
            user.Last_Out = timezone.now()
            updated_users.append(user)
            
            # Create activity log
            updated_logs.append(models.ActivityLog(
                user_id=user.User_ID,
                operation='Check Out',
                status='Success',
            ))
        
        if updated_users:
            models.Users.objects.bulk_update(
                updated_users, 
                ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out"]
            )
            models.ActivityLog.objects.bulk_create(updated_logs)
            logger.info(f"Checked out {len(updated_users)} users via admin action")


@admin.action(description="Check In Members")
def check_in(modeladmin, request, queryset):
    """
    Admin action to check in selected users.
    
    Updates user records and creates activity logs atomically.
    """
    with transaction.atomic():
        checked_out_users = queryset.select_for_update().filter(Checked_In=False)
        updated_users = []
        updated_logs = []
        
        for user in checked_out_users:
            user.Checked_In = True
            user.Last_In = timezone.now()
            updated_users.append(user)
            
            # Create activity log
            updated_logs.append(models.ActivityLog(
                user_id=user.User_ID,
                operation='Check In',
                status='Success',
            ))
        
        if updated_users:
            models.Users.objects.bulk_update(
                updated_users, 
                ["Checked_In", "Last_In"]
            )
            models.ActivityLog.objects.bulk_create(updated_logs)
            logger.info(f"Checked in {len(updated_users)} users via admin action")


@admin.action(description="Reset Members")
def reset(modeladmin, request, queryset):
    """
    Admin action to reset user hours and check-in status.
    
    Resets all time tracking fields and checks out users if needed.
    """
    with transaction.atomic():
        users_to_update = queryset.select_for_update()
        updated_users = []
        updated_logs = []
        
        for user in users_to_update:
            # If user is checked in, check them out first
            if user.Checked_In:
                updated_logs.append(models.ActivityLog(
                    user_id=user.User_ID,
                    operation='Check Out',
                    status='Success',
                ))
                user.Checked_In = False
            
            # Reset all time tracking fields
            user.Total_Seconds = 0
            user.Total_Hours = '0:00:00'
            user.Last_In = None
            user.Last_Out = None
            updated_users.append(user)
            
            # Create reset log
            updated_logs.append(models.ActivityLog(
                user_id=user.User_ID,
                operation='Reset',
                status='Success',
            ))
        
        if updated_users:
            models.Users.objects.bulk_update(
                updated_users,
                ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out", "Last_In"]
            )
            models.ActivityLog.objects.bulk_create(updated_logs)
            logger.info(f"Reset {len(updated_users)} users via admin action")


def create_staff_user_action(modeladmin, request, queryset):
    """Admin action to create a staff user from selected member."""
    selected_user = queryset.first()
    
    if not selected_user:
        logger.warning("No user selected for staff creation")
        return
    
    form = CustomActionForm()
    form.fields['hidden_data'].initial = json.dumps({
        'First_Name': selected_user.First_Name,
        'Last_Name': selected_user.Last_Name,
        'User_ID': selected_user.User_ID
    })
    
    context = {
        'form': form,
        'user': selected_user,
        'title': 'Create Staff User',
    }
    
    from django.template.response import TemplateResponse
    return TemplateResponse(request, 'admin/custom_action_form.html', context)


create_staff_user_action.short_description = "Create Staff User"


class CheckedInFilter(SimpleListFilter):
    """Custom filter for checked-in status in admin list view."""
    title = 'Checked In Status'
    parameter_name = 'checked_in'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Checked In'),
            ('no', 'Checked Out'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(Checked_In=True)
        if self.value() == 'no':
            return queryset.filter(Checked_In=False)
        return queryset


class ActiveFilter(SimpleListFilter):
    """Custom filter for active status in admin list view."""
    title = 'Active Status'
    parameter_name = 'is_active'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Active'),
            ('no', 'Inactive'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(Is_Active=True)
        if self.value() == 'no':
            return queryset.filter(Is_Active=False)
        return queryset


class MemberAdmin(admin.ModelAdmin):
    """Admin configuration for Users model."""
    
    list_display = ('User_ID', 'First_Name', 'Last_Name', 'Checked_In', 
                   'Total_Hours', 'Is_Active')
    list_filter = (CheckedInFilter, ActiveFilter)
    search_fields = ('User_ID', 'First_Name', 'Last_Name')
    ordering = ('User_ID',)
    actions = [check_in, check_out, reset, create_staff_user_action]
    
    fieldsets = (
        ('User Information', {
            'fields': ('User_ID', 'First_Name', 'Last_Name', 'Is_Active')
        }),
        ('Check-In Status', {
            'fields': ('Checked_In', 'Last_In', 'Last_Out')
        }),
        ('Time Tracking', {
            'fields': ('Total_Hours', 'Total_Seconds')
        }),
    )
    
    readonly_fields = ('Total_Hours',)


class UserIDFilter(SimpleListFilter):
    """Custom filter for User ID in activity log."""
    title = 'User ID'
    parameter_name = 'user_id'

    def lookups(self, request, model_admin):
        # Get all unique user IDs
        user_ids = ActivityLog.objects.values_list('user_id', flat=True).distinct()
        return [(uid, uid) for uid in user_ids if uid]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user_id=self.value())
        return queryset


class OperationFilter(SimpleListFilter):
    """Custom filter for operation type in activity log."""
    title = 'Operation'
    parameter_name = 'operation'

    def lookups(self, request, model_admin):
        operations = ActivityLog.objects.values_list('operation', flat=True).distinct()
        return [(op, op) for op in operations if op]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(operation=self.value())
        return queryset


class ActivityAdminView(admin.ModelAdmin):
    """Admin configuration for ActivityLog model."""
    
    list_display = ('user_id', 'operation', 'status', 'timestamp')
    list_filter = (OperationFilter, 'status', UserIDFilter)
    search_fields = ('user_id', 'operation', 'status', 'message')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user_id', 'entered', 'operation', 'status')
        }),
        ('Details', {
            'fields': ('message', 'timestamp')
        }),
    )
    
    readonly_fields = ('timestamp',)


def is_superuser(user):
    """Check if user is a superuser for access control."""
    return user.is_superuser


@user_passes_test(is_superuser)
def add_user(request):
    """
    View for creating a new staff user from admin panel.
    
    Requires superuser privileges. Creates a Django auth user and assigns
    them to the specified group.
    """
    if request.method != 'POST':
        return redirect('/admin/')
    
    try:
        form_data_dict = request.POST.dict()
        form_data = SimpleNamespace(**form_data_dict)
        
        username = form_data.username
        password = form_data.password
        group_name = form_data.group_name
        hidden_data = json.loads(form_data.hidden_data)
        fname = hidden_data['First_Name']
        lname = hidden_data['Last_Name']
        
        # Check if user already exists
        if authModels.User.objects.filter(username=username).exists():
            logger.warning(f"Attempted to create duplicate user: {username}")
            # Could add a message framework message here
        else:
            # Create user with transaction safety
            with transaction.atomic():
                user = authModels.User.objects.create_user(
                    username=username,
                    first_name=fname,
                    last_name=lname
                )
                user.set_password(raw_password=password)
                user.is_staff = True
                user.save()
                
                # Add user to group
                group = authModels.Group.objects.get(name=group_name)
                user.groups.add(group)
                
                logger.info(f"Created new staff user: {username} in group: {group_name}")
    
    except Exception as e:
        logger.error(f"Error creating staff user: {str(e)}")
    
    return redirect('/admin/')


# Register models with admin site
admin.site.register(model_or_iterable=Users, admin_class=MemberAdmin)
admin.site.register(model_or_iterable=ActivityLog, admin_class=ActivityAdminView)