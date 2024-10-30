import csv
import json
from datetime import datetime
from types import SimpleNamespace

import django.contrib.auth.models as authModels
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.decorators import user_passes_test
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from HeroHours.forms import CustomActionForm
from . import models
from .models import Users, ActivityLog
from rest_framework.authtoken.admin import TokenAdmin


# Register your models here.


TokenAdmin.raw_id_fields = ['user']

@admin.action(description="Check Out Users")
def check_out(modeladmin, request, queryset):
    getall = queryset.filter(Checked_In=True)
    updated_users = []
    updated_log = []
    for user in getall:
        lognew = models.ActivityLog(
            userID=user.User_ID,
            operation='Check Out',
            status='Success',  # Initial status
        )
        user.Checked_In = False
        user.Total_Hours = (
                datetime.combine(datetime.today(), user.Total_Hours) + (timezone.now() - user.Last_In)).time()
        #print((timezone.now() - user.Last_In).total_seconds())
        user.Total_Seconds += round((timezone.now() - user.Last_In).total_seconds())
        user.Last_Out = timezone.now()
        updated_log.append(lognew)
        updated_users.append(user)
    models.Users.objects.bulk_update(updated_users, ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out"])
    models.ActivityLog.objects.bulk_create(updated_log)


@admin.action(description="Check In Users")
def check_in(modeladmin, request, queryset):
    updated_users = []
    updated_log = []
    getall = queryset.filter(Checked_In=False)
    for user in getall:
        lognew = models.ActivityLog(
            userID=user.User_ID,
            operation='Check In',
            status='Success',  # Initial status
        )
        user.Checked_In = True
        user.Last_In = timezone.now()
        updated_log.append(lognew)
        updated_users.append(user)
    models.Users.objects.bulk_update(updated_users, ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out"])
    models.ActivityLog.objects.bulk_create(updated_log)


def create_staff_user_action(modeladmin, request, queryset):
    print(request)
    selected_user = queryset.first()
    userdata = model_to_dict(selected_user)

    form = CustomActionForm(
        initial={'hidden_data': json.dumps({'First_Name': userdata['First_Name'], 'Last_Name': userdata['Last_Name']})})
    return render(request, 'admin/custom_action_form.html', {'form': form})


create_staff_user_action.short_description = "Create a Staff User"


class TotalHoursFilter(SimpleListFilter):
    title = _('total hours less than')  # Display title in the admin filter sidebar
    parameter_name = 'total_hours'  # URL parameter

    def lookups(self, request, model_admin):
        # Options for filtering by hours
        return [
            ('1hour', _('Less than 1 hour')),
            ('5hours', _('Less than 5 hours')),
            ('10hours', _('Less than 10 hours')),
        ]

    def queryset(self, request, queryset):
        # Filtering based on 'Total_Seconds' (since 1 hour = 3600 seconds)
        if self.value() == '1hour':
            return queryset.filter(Total_Seconds__lt=3600)
        elif self.value() == '5hours':
            return queryset.filter(Total_Seconds__lt=3600 * 5)
        elif self.value() == '10hours':
            return queryset.filter(Total_Seconds__lt=3600 * 10)
        return queryset


@admin.action(description="Export Selected")
def export_as_csv(self, request, queryset):
    meta = self.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        row = writer.writerow([getattr(obj, field) for field in field_names])

    return response


class UsersAdmin(admin.ModelAdmin):
    list_display = ("User_ID", "First_Name", "Last_Name", "Is_Active", "Checked_In", "display_total_hours")
    readonly_fields = ["Checked_In", "Last_In", "Last_Out"]
    data_hierarchy = "Last_Name"
    actions = [check_out, check_in, export_as_csv, create_staff_user_action]
    search_fields = ['User_ID', 'Last_Name', 'First_Name']
    list_filter = ['Checked_In', TotalHoursFilter]

    def display_total_hours(self, obj):
        return obj.get_total_hours()

    display_total_hours.short_description = "Total Hours"
    display_total_hours.admin_order_field = "Total_Seconds"


class ActivityAdminView(admin.ModelAdmin):
    list_display = ('userID', 'get_name', 'get_op', 'get_status', 'timestamp', 'get_date_only')
    search_fields = ['timestamp']

    def get_date_only(self, obj):
        return timezone.localtime(obj.timestamp).date()

    get_date_only.short_description = 'Date'

    def get_name(self, obj):
        names = Users.objects.only('First_Name', 'Last_Name').get(User_ID=obj.userID)
        #TODO fix this
        #this is extremely slow - just a quick addition that will need to be optimized
        #it queries for each log, which is bad.
        return f'{names.First_Name} {names.Last_Name}'
    get_name.short_description = 'Name'

    def get_status(self, obj):
        return obj.status

    get_status.short_description = 'Status'

    def get_op(self, obj):
        return obj.operation

    get_op.short_description = 'Operation'


def is_superuser(user):
    return user.is_superuser


@user_passes_test(is_superuser)
def add_user(request):
    form_data_dict = request.POST.dict()
    form_data = SimpleNamespace(**form_data_dict)
    print(form_data)
    username = form_data.username
    password = form_data.password
    hidden_data = json.loads(form_data.hidden_data)
    fname = hidden_data['First_Name']
    lname = hidden_data['Last_Name']
    group_name = form_data.group_name

    if authModels.User.objects.filter(username=username).exists():
        print('User already exists')
    else:
        user = authModels.User.objects.create_user(username=username,
                                                   first_name=fname,
                                                   last_name=lname)
        user.set_password(raw_password=password)
        user.is_staff = True
        user.save()

        group = authModels.Group.objects.get(name=group_name)
        print(group)
        user.groups.add(group)

        print('nicely done')

    return redirect('/admin/')


# Custom action to create a staff user

admin.site.register(model_or_iterable=Users, admin_class=UsersAdmin)
admin.site.register(model_or_iterable=ActivityLog, admin_class=ActivityAdminView)
admin.site.site_header = 'HERO Hours Admin'
admin.site.site_title = 'HERO Hours Admin'
admin.site.index_title = 'User Administration'
