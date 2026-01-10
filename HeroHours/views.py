"""
HeroHours Views Module
======================

This module handles all web requests for the HeroHours attendance tracking system.

Main Functionalities:
- User check-in/check-out operations
- Bulk operations for checking all users in or out
- Google Sheets integration for data backup
- Live view for real-time attendance monitoring

Maintenance Notes:
- All database operations use transactions for data integrity
- Special commands are defined in Commands constant class
- Status/operation strings use constants from StatusMessages and Operations classes
"""
import base64
import json
import logging
import os
from typing import Optional, Dict, Any

import requests
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import permission_required, login_required
from django.core import serializers
from django.core.exceptions import BadRequest, PermissionDenied
from django.db import transaction
from django.forms.models import model_to_dict
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from dotenv import load_dotenv, find_dotenv

from . import models

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)

# Constants for maintainability - Cached as tuples for faster lookup
class Commands:
    """Special command constants for the attendance system"""
    SEND_TO_SHEETS = "Send"
    REFRESH_PAGE = ('+00', '+01', '*')  # Tuple is faster than list for membership tests
    ADMIN_PANEL = "admin"
    LOGOUT = "---"
    BULK_CHECK_IN = "-404"  # Debug mode only
    BULK_CHECK_OUT = "+404"
    
    # Pre-compiled set for O(1) lookups
    _REFRESH_SET = frozenset(REFRESH_PAGE)
    
    @classmethod
    def is_refresh_command(cls, cmd: str) -> bool:
        """Fast O(1) check if command is a refresh command"""
        return cmd in cls._REFRESH_SET

class StatusMessages:
    """Standard status messages for consistency"""
    SUCCESS = 'Success'
    ERROR = 'Error'
    USER_NOT_FOUND = 'User Not Found'
    INVALID_INPUT = 'Invalid Input'
    INACTIVE_USER = 'Inactive User'
    CHECK_OUT = 'Check Out'

class Operations:
    """Operation type constants"""
    CHECK_IN = 'Check In'
    CHECK_OUT = 'Check Out'
    NONE = 'None'

# Configuration
APP_SCRIPT_URL = os.environ.get('APP_SCRIPT_URL', '')


@staff_member_required
@permission_required("HeroHours.change_users")
def index(request) -> HttpResponse:
    """
    Display the main dashboard with active users and recent activity.
    
    This view shows:
    - All active users with their check-in status
    - Count of currently checked-in users
    - 9 most recent activity log entries
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Rendered HTML page with user and activity data
        
    Permissions:
        Requires 'HeroHours.change_users' permission
        
    Performance:
        - Uses only() to fetch only required fields
        - Uses select_related for join optimization
        - Single query for checked_in count
    """
    # Microoptimization: Use only() to fetch only needed fields from DB
    users_data = models.Users.objects.filter(
        Is_Active=True
    ).only(
        'User_ID', 'First_Name', 'Last_Name', 'Checked_In', 
        'Total_Seconds', 'Last_In', 'Last_Out'
    ).order_by('Last_Name', 'First_Name')
    
    # Microoptimization: Use exists() if we only need count, but count() is already optimized
    users_checked_in = models.Users.objects.filter(Checked_In=True, Is_Active=True).count()
    
    # Microoptimization: select_related for single query instead of N+1
    local_log_entries = models.ActivityLog.objects.select_related('user').only(
        'id', 'entered', 'operation', 'status', 'timestamp',
        'user__User_ID', 'user__First_Name', 'user__Last_Name'
    )[:9]
    
    return render(request, 'members.html', {
        'usersData': users_data,
        'checked_in': users_checked_in,
        'local_log_entries': local_log_entries
    })

@staff_member_required
@permission_required("HeroHours.change_users", raise_exception=True)
def handle_entry(request) -> JsonResponse:
    """
    Process user check-in/check-out requests and special commands.
    
    This is the main entry point for attendance operations. It handles:
    - User check-in and check-out by ID
    - Special commands (Send, admin, logout, refresh)
    - Bulk operations (+404 to check all out, -404 to check all in)
    - Input validation and error handling
    
    Args:
        request: Django HTTP request with 'user_input' in POST data
        
    Returns:
        JsonResponse with operation result or redirect for special commands
        
    Response Format:
        Success: {
            'status': 'Success' or 'Check Out',
            'state': true/false,
            'newlog': {...log data...},
            'count': number of checked-in users
        }
        Error: {
            'status': 'Error' or 'User Not Found' or 'Invalid Input',
            'newlog': {...log data...},
            'count': number of checked-in users
        }
    
    Permissions:
        Requires 'HeroHours.change_users' permission
        
    Performance:
        - Early returns for special commands (avoids DB queries)
        - Cached count query
        - Single user lookup with filter().first()
    """
    user_input = request.POST.get('user_input', '').strip()
    
    # Microoptimization: Early return for empty input (avoid processing)
    if not user_input:
        return JsonResponse({
            'status': StatusMessages.ERROR,
            'message': 'No input provided'
        }, status=400)
    
    # Microoptimization: Handle special commands first to avoid DB queries
    special_result = _handle_special_commands(user_input, request)
    if special_result:
        return special_result
    
    # Microoptimization: Check bulk operations before DB operations
    if user_input in (Commands.BULK_CHECK_IN, Commands.BULK_CHECK_OUT):
        right_now = timezone.now()
        return _handle_bulk_updates(user_input, right_now)
    
    # Now we know it's a regular check-in/out, get timestamp
    right_now = timezone.now()
    
    # Get current check-in count (cached for response)
    count = _get_checked_in_count()
    
    # Initialize activity log for tracking
    log = models.ActivityLog(
        entered=user_input,
        operation=Operations.NONE,
        status=StatusMessages.ERROR,
    )
    
    try:
        # Microoptimization: Use try/except for int conversion (EAFP - faster for valid inputs)
        try:
            user_id = int(user_input)
        except ValueError:
            log.status = StatusMessages.INVALID_INPUT
            log.save()
            return JsonResponse({
                'status': StatusMessages.INVALID_INPUT,
                'user_id': None,
                'operation': None,
                'newlog': model_to_dict(log),
                'count': count
            })
        
        # Microoptimization: Use filter().first() instead of get() to avoid exception overhead
        user = models.Users.objects.filter(User_ID=user_id).first()
        log.user = user
        
        if not user:
            log.status = StatusMessages.USER_NOT_FOUND
            log.save()
            return JsonResponse({
                'status': StatusMessages.USER_NOT_FOUND,
                'user_id': None,
                'operation': None,
                'newlog': model_to_dict(log),
                'count': count
            })
        
        # Perform Check-In or Check-Out operation
        operation_result = _process_check_in_out(user, right_now, log, count)
        return JsonResponse(operation_result)
        
    except Exception as e:
        logger.error(f"Error in handle_entry: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'status': StatusMessages.ERROR,
            'newlog': {
                'entered': user_input,
                'operation': Operations.NONE,
                'status': StatusMessages.ERROR,
                'message': 'An unexpected error occurred'
            },
            'state': None,
            'count': count
        }, status=500)


def _handle_special_commands(user_input: str, request) -> Optional[HttpResponse]:
    """
    Process special command inputs.
    
    Special commands are non-numeric inputs that trigger specific actions:
    - "Send": Export data to Google Sheets
    - "+00", "+01", "*": Refresh the page
    - "admin": Navigate to admin panel
    - "---": Logout current user
    
    Args:
        user_input: The command string to process
        request: Django HTTP request object (for logout)
        
    Returns:
        HttpResponse for redirect or None if not a special command
        
    Performance:
        Uses optimized string comparisons in order of likelihood
    """
    # Microoptimization: Check most common commands first
    if Commands.is_refresh_command(user_input):  # O(1) lookup
        return redirect('index')
    
    if user_input == Commands.SEND_TO_SHEETS:
        return redirect('send_data_to_google_sheet')
    
    if user_input == Commands.ADMIN_PANEL:
        return redirect('/admin/')
    
    if user_input == Commands.LOGOUT:
        logout(request)
        return redirect('login')
    
    return None


def _handle_bulk_updates(user_id: str, time=None) -> HttpResponse:
    """
    Perform bulk check-in or check-out operations for all active users.
    
    Bulk operations:
    - "-404": Check in all users who are currently checked out (DEBUG MODE ONLY)
    - "+404": Check out all users who are currently checked in
    
    All operations are atomic (wrapped in a database transaction).
    
    Args:
        user_id: Either "-404" (bulk check-in) or "+404" (bulk check-out)
        time: Timestamp for the operation (defaults to now)
        
    Returns:
        Redirect to index page
        
    Side Effects:
        - Updates Checked_In status for all active users
        - Creates ActivityLog entries for each user
        - For check-outs: Updates Total_Seconds, Total_Hours, and Last_Out
        - For check-ins: Updates Last_In
    """
    if time is None:
        time = timezone.now()
    
    # -404 is a debug-only feature to check everyone in
    if user_id == Commands.BULK_CHECK_IN:
        if not os.environ.get('DEBUG', 'False') == 'True':
            return redirect('index')
        users_to_update = models.Users.objects.filter(Checked_In=False, Is_Active=True)
        operation = Operations.CHECK_IN
    else:
        # +404 checks everyone out
        users_to_update = models.Users.objects.filter(Checked_In=True, Is_Active=True)
        operation = Operations.CHECK_OUT
    
    updated_users = []
    updated_logs = []
    
    # Use transaction to ensure atomicity
    with transaction.atomic():
        for user in users_to_update:
            log = models.ActivityLog(
                user=user,
                entered=str(user.User_ID),
                operation=operation,
                status=StatusMessages.SUCCESS
            )
            
            if user_id == Commands.BULK_CHECK_IN:
                # Check everyone in
                user.Checked_In = True
                user.Last_In = time
            else:
                # Check everyone out
                if not user.Last_In:
                    user.Last_In = time
                
                # Calculate time delta and update totals
                time_delta = (time - user.Last_In).total_seconds()
                user.Total_Seconds += time_delta
                user.Total_Hours = timezone.timedelta(seconds=user.Total_Seconds)
                user.Last_Out = time
                user.Checked_In = False
            
            updated_users.append(user)
            updated_logs.append(log)
        
        # Bulk update all users
        if user_id == Commands.BULK_CHECK_IN:
            models.Users.objects.bulk_update(updated_users, ["Checked_In", "Last_In"])
        else:
            models.Users.objects.bulk_update(updated_users, ["Checked_In", "Total_Hours", "Total_Seconds", "Last_Out"])
        
        # Bulk create all logs
        models.ActivityLog.objects.bulk_create(updated_logs)
    
    return redirect('index')


def _process_check_in_out(user: models.Users, right_now, log: models.ActivityLog, count: int) -> Dict[str, Any]:
    """
    Process a user's check-in or check-out operation.
    
    This function determines whether to check a user in or out based on their
    current status, then performs the operation atomically using database transactions
    with row-level locking to prevent race conditions.
    
    Args:
        user: The Users model instance to check in/out
        right_now: Timestamp for the operation
        log: ActivityLog instance to be updated and saved
        count: Current count of checked-in users
        
    Returns:
        Dictionary with operation results:
        {
            'status': Status message ('Success', 'Check Out', or 'Inactive User'),
            'state': True (checked in), False (checked out), or None (inactive),
            'newlog': Serialized log entry,
            'count': Updated count of checked-in users
        }
        
    Side Effects:
        - Updates user's Checked_In status
        - For check-out: Updates Total_Seconds, Total_Hours, Last_Out
        - For check-in: Updates Last_In
        - Saves ActivityLog entry
        
    Transaction Safety:
        Uses select_for_update() to acquire row-level lock, preventing
        concurrent modifications that could corrupt time calculations.
    """
    count2 = count
    
    # Early return for inactive users
    if not user.Is_Active:
        log.operation = Operations.NONE
        log.status = StatusMessages.INACTIVE_USER
        log.save()
        return {
            'status': log.status,
            'state': None,
            'newlog': model_to_dict(log),
            'count': count,
        }
    
    # Use transaction to ensure atomicity and prevent race conditions
    with transaction.atomic():
        # Refresh user from DB with row-level lock
        user = models.Users.objects.select_for_update().get(pk=user.pk)
        
        if user.Checked_In:
            # User is checking out
            count2 -= 1
            state = False
            log.operation = Operations.CHECK_OUT
            
            # Handle edge case of missing Last_In timestamp
            if not user.Last_In:
                user.Last_In = right_now
            
            # Calculate session duration
            time_delta = (right_now - user.Last_In).total_seconds()
            
            # Update user fields directly (not using F() to avoid race conditions)
            user.Total_Seconds += time_delta
            user.Total_Hours = timezone.timedelta(seconds=user.Total_Seconds)
            user.Last_Out = right_now
            user.Checked_In = False
        else:
            # User is checking in
            count2 += 1
            state = True
            log.operation = Operations.CHECK_IN
            user.Last_In = right_now
            user.Checked_In = True
        
        user.save()
        count = count2
        log.status = StatusMessages.SUCCESS
    
    # Save log after transaction completes
    log.save()
    
    # Determine status message for response
    operation = StatusMessages.CHECK_OUT if not state else StatusMessages.SUCCESS
    return {
        'status': operation,
        'state': state,
        'newlog': model_to_dict(log),
        'count': count,
    }


def _get_checked_in_count() -> int:
    """
    Get the current count of checked-in active users.
    
    Returns:
        Number of users with Is_Active=True and Checked_In=True
    """
    return models.Users.objects.filter(Checked_In=True, Is_Active=True).count()


@staff_member_required
@permission_required("HeroHours.change_users", raise_exception=True)
def send_data_to_google_sheet(request) -> JsonResponse:
    """
    Export user and activity log data to Google Sheets.
    
    This function serializes all users and activity logs, then sends them
    to a Google Apps Script endpoint for processing and storage in Google Sheets.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        JsonResponse with export status and checked-in count
        
    Response Format:
        Success: {
            'status': 'Sent',
            'result': {...response from Google Sheets...},
            'count': number of checked-in users
        }
        Failure: {
            'status': 'error',
            'message': error description,
            'count': number of checked-in users
        }
        
    Environment Variables:
        APP_SCRIPT_URL: URL of the Google Apps Script web app endpoint
        
    Permissions:
        Requires 'HeroHours.change_users' permission
    """
    users = models.Users.objects.all()
    serialized_users = serializers.serialize('json', users, use_natural_foreign_keys=True)
    serialized_logs = serializers.serialize('json', models.ActivityLog.objects.all(), use_natural_foreign_keys=True)
    
    data_package = [serialized_users, serialized_logs]
    all_data = json.dumps(obj=data_package)
    count = users.filter(Checked_In=True, Is_Active=True).count()

    try:
        response = requests.post(APP_SCRIPT_URL, json=json.loads(all_data), timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return JsonResponse({
                'status': 'Sent',
                'result': result,
                'count': count
            })
        else:
            logger.warning(f"Google Sheets export failed with status {response.status_code}")
            return JsonResponse({
                'status': 'Sent',
                'message': 'Failed to send data',
                'count': count
            })
    except Exception as e:
        logger.error(f"Error sending to Google Sheets: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e),
            'count': count
        })


@login_required
def sheet_pull(request) -> HttpResponse:
    """
    Export user data as CSV for Google Sheets integration.
    
    This endpoint allows Google Sheets to pull user data via authenticated
    CSV export. Authentication uses a base64-encoded username:password key.
    
    Args:
        request: Django HTTP request with 'key' parameter in GET
        
    Returns:
        CSV formatted user data
        
    Raises:
        BadRequest: If 'key' parameter is missing or malformed
        PermissionDenied: If authentication fails
        
    URL Parameters:
        key: Base64-encoded "username:password" string
        
    CSV Format:
        Headers: User_ID, First_Name, Last_Name, Total_Hours, Total_Seconds,
                Last_In, Last_Out, Is_Active
    """
    key = request.GET.get('key')
    if not key:
        raise BadRequest("Missing authentication key")

    try:
        username, password = base64.b64decode(key).decode('ascii').split(":", 1)
    except Exception:
        raise BadRequest("Invalid key format")
    
    user = authenticate(request, username=username, password=password)
    if not user:
        logger.warning(f"Failed authentication attempt for sheet_pull from {request.META.get('REMOTE_ADDR')}")
        raise PermissionDenied()
    
    members = models.Users.objects.all().order_by('User_ID')
    csv_lines = ['User_ID,First_Name,Last_Name,Total_Hours,Total_Seconds,Last_In,Last_Out,Is_Active\n']
    
    for member in members:
        csv_lines.append(
            f"{member.User_ID},"
            f"{member.First_Name},"
            f"{member.Last_Name},"
            f"{member.get_total_hours()},"
            f"{member.Total_Seconds},"
            f"{member.Last_In or ''},"
            f"{member.Last_Out or ''},"
            f"{member.Is_Active}\n"
        )
    
    return HttpResponse(''.join(csv_lines), content_type='text/csv')


def logout_view(request) -> HttpResponse:
    """
    Log out the current user and redirect to login page.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Redirect to the login page
    """
    logout(request)
    return redirect('login')


@staff_member_required
@permission_required("HeroHours.change_users")
def live_view(request) -> HttpResponse:
    """
    Display the live attendance monitoring view.
    
    This view shows real-time attendance updates using WebSocket connections.
    Users can see check-in/check-out events as they happen.
    
    Args:
        request: Django HTTP request object
        
    Returns:
        Rendered live.html template
        
    Permissions:
        Requires 'HeroHours.change_users' permission
        
    Note:
        Requires WebSocket consumer (consumers.py) to be properly configured
        for real-time updates to function.
    """
    return render(request, 'live.html')
    return render(request, 'live.html')