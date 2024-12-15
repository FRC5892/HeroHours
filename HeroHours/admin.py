import csv
import json
from datetime import datetime
from types import SimpleNamespace

import django.contrib.auth.models as authModels
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied, BadRequest
from django.forms import model_to_dict
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import capfirst
from HeroHours.forms import CustomActionForm
from . import models
from .models import Users, ActivityLog
from rest_framework.authtoken.admin import TokenAdmin
from django.contrib.admin.utils import (unquote)
from django.contrib.admin.options import get_content_type_for_model
from django.template.response import TemplateResponse
from django.urls import path
# Register your models here.


TokenAdmin.raw_id_fields = ['user']

@admin.action(description="Check Out Users")
def check_out(modeladmin, request, queryset):
    getall = queryset.filter(Checked_In=True)
    updated_users = []
    updated_log = []
    for user in getall:
        lognew = models.ActivityLog(
            user_id=user.User_ID,
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
            user_id=user.User_ID,
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
    title = _('Total Hours')  # Display title in the admin filter sidebar
    parameter_name = 'total_hours'  # URL parameter

    def lookups(self, request, model_admin):
        # Options for filtering by hours
        return [
            ('1hour', _('Less than 1 hour')),
            ('5hours', _('Less than 5 hours')),
            ('10hours', _('Less than 10 hours')),
            ('25hours', _('Less than 25 hours')),

            ('o25hours', _('Over 25 hours')),
            ('o50hours',_('Over 50 hours'))
        ]

    def queryset(self, request, queryset):
        """Filter by hours using the stored Total Seconds"""
        # Negative numbers mean less than, positive is greater than
        under_values = {
            '1hour':-3600,
            '5hours':-3600*5,
            '10hours':-3600*10,
            '25hours':-3600*25,
            'o25hours':3600*25,
            'o50hours':3600*50
        }
        seconds = under_values.get(self.value())
        if seconds is None:
            # Not for us
            return queryset

        if seconds < 1:
            return queryset.filter(Total_Seconds__lt=-seconds)
        else:
            return queryset.filter(Total_Seconds__gt=seconds)


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
    actions = [check_out, check_in, export_as_csv]
    search_fields = ['User_ID', 'Last_Name', 'First_Name']
    list_filter = ['Checked_In', TotalHoursFilter]

    def get_urls(self):
        urls = super().get_urls()
        info = self.opts.app_label, self.opts.model_name
        my_urls = [
            # path("promote/", self.admin_site.admin_view(self.promote_to_staff_view),name="promote"),
            path(
                "<path:object_id>/promote/",
                self.admin_site.admin_view(self.promote_to_staff_view),
                name="%s_%s_promote" % info,
            ),
        ]
        return my_urls + urls
    def promote_to_staff_view(self, request, object_id, extra_context=None):
        member = get_object_or_404(Users,User_ID=object_id)



        return render(request, 'admin/custom_action_form.html', {})



    def display_total_hours(self, obj):
        return obj.get_total_hours()

    display_total_hours.short_description = "Total Hours"
    display_total_hours.admin_order_field = "Total_Seconds"


    """
        Custom history view, modified from Django source
        
        Copyright (c) Django Software Foundation and individual contributors.
        All rights reserved.
        
        Redistribution and use in source and binary forms, with or without modification,
        are permitted provided that the following conditions are met:
        
            1. Redistributions of source code must retain the above copyright notice,
               this list of conditions and the following disclaimer.
        
            2. Redistributions in binary form must reproduce the above copyright
               notice, this list of conditions and the following disclaimer in the
               documentation and/or other materials provided with the distribution.
        
            3. Neither the name of Django nor the names of its contributors may be used
               to endorse or promote products derived from this software without
               specific prior written permission.
        
        THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
        ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
        WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
        DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
        ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
        (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
        LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
        ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
        (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
        SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """
    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from django.contrib.admin.views.main import PAGE_VAR

        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            return self._get_obj_does_not_exist_redirect(
                request, model._meta, object_id
            )

        if not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        app_label = self.opts.app_label
        action_list = (
            ActivityLog.objects.filter( # modified
                user_id=unquote(object_id), # modified
            )
            .select_related()
            .order_by('timestamp')
        )

        paginator = self.get_paginator(request, action_list, 100)
        page_number = request.GET.get(PAGE_VAR, 1)
        page_obj = paginator.get_page(page_number)
        page_range = paginator.get_elided_page_range(page_obj.number)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Change history: %s") % obj,
            "subtitle": None,
            "action_list": page_obj,
            "page_range": page_range,
            "page_var": PAGE_VAR,
            "pagination_required": paginator.count > 100,
            "module_name": str(capfirst(self.opts.verbose_name_plural)),
            "object": obj,
            "opts": self.opts,
            "preserved_filters": self.get_preserved_filters(request),
            **(extra_context or {}),
        }

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.object_history_template
            or [
                "admin/%s/%s/object_history.html" % (app_label, self.opts.model_name),
                "admin/%s/object_history.html" % app_label,
                "admin/object_history.html",
                ],
            context,
            )


class ActivityAdminView(admin.ModelAdmin):
    list_display = ('get_entered_data', 'get_name', 'get_op', 'get_status', 'timestamp', 'get_date_only')
    readonly_fields = ('user','entered','status','operation','message')
    search_fields = ['timestamp']

    def get_date_only(self, obj):
        return timezone.localtime(obj.timestamp).date()
    def get_entered_data(self, obj):
        return obj.entered
    get_entered_data.short_description = 'Entered'


    get_date_only.short_description = 'Date'

    def get_name(self, obj):
        if obj.user:
            return f'{obj.user.First_Name} {obj.user.Last_Name}'
        return  'None'
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
