import csv

from django.contrib import admin
from django.http import HttpResponse
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from . import models
from datetime import datetime
from django.utils import timezone


# Register your models here.


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


class UserAdmin(admin.ModelAdmin):
    list_display = ("User_ID", "First_Name", "Last_Name", "Checked_In", "display_total_hours")
    readonly_fields = ["Checked_In","Last_In","Last_Out"]
    data_hierarchy = "Last_Name"
    actions = [check_out, check_in,export_as_csv]
    search_fields = ['User_ID', 'Last_Name', 'First_Name']
    list_filter = ['Checked_In', TotalHoursFilter]
    def display_total_hours(self, obj):
            return obj.get_total_hours()
    display_total_hours.short_description = "Total Hours"
    display_total_hours.admin_order_field = "Total_Seconds"



admin.site.register(models.Users, UserAdmin)
admin.site.site_header = 'HERO Hours Admin'
admin.site.site_title = 'HERO Hours Admin'
admin.site.index_title = 'User Administration'