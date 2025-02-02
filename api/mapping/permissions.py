import os
from typing import Any
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from rest_framework import permissions
from rest_framework.request import Request
from .models import (
    Dataset,
    ScanReport,
    ScanReportField,
    ScanReportTable,
    ScanReportValue,
    VisibilityChoices,
)


# Get scan report for the table|field|value
SCAN_REPORT_QUERIES = {
    ScanReportTable: lambda x: ScanReport.objects.get(id=x.scan_report.id),
    ScanReportField: lambda x: ScanReport.objects.get(
        id=x.scan_report_table.scan_report.id
    ),
    ScanReportValue: lambda x: ScanReport.objects.get(
        id=x.scan_report_field.scan_report_table.scan_report.id
    ),
}


def is_az_function_user(user: User) -> bool:
    """Check of the user is the `AZ_FUNCTION_USER`

    Args:
        user (User): The user to check

    Returns:
        bool: `True` if `user` is the `AZ_FUNCTION_USER` else `False`
    """

    return user.username == os.getenv("AZ_FUNCTION_USER")


def has_viewership(obj: Any, request: Request) -> bool:
    """Check the viewership permission on an object.

    Args:
        obj (Any): The object to check the permissions on.
        request (Request): The request with the User instance.

    Returns:
        bool: `True` if the request's user has permission, else `False`.
    """
    # Permission checks to perform
    checks = {
        Dataset: lambda x: Dataset.objects.filter(
            Q(visibility=VisibilityChoices.PUBLIC)
            | Q(viewers__id=request.user.id, visibility=VisibilityChoices.RESTRICTED)
            | Q(editors__id=request.user.id, visibility=VisibilityChoices.RESTRICTED)
            | Q(admins__id=request.user.id, visibility=VisibilityChoices.RESTRICTED),
            project__members__id=request.user.id,
            id=x.id,
        ).exists(),
        ScanReport: lambda x: ScanReport.objects.filter(
            # parent dataset and SR are public checks
            Q(
                # parent dataset and SR are public
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                visibility=VisibilityChoices.PUBLIC,
            )
            # parent dataset is public but SR restricted checks
            | Q(
                # parent dataset is public
                # SR is restricted and user is in SR viewers
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                viewers=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset is public
                # SR is restricted and user is in SR editors
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                editors=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset is public
                # SR is restricted and user is SR author
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                author=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset is public
                # SR is restricted and user is in parent dataset editors
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                parent_dataset__editors=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset is public
                # SR is restricted and user is in parent dataset admins
                parent_dataset__visibility=VisibilityChoices.PUBLIC,
                parent_dataset__admins=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            # parent dataset and SR are restricted checks
            | Q(
                # parent dataset and SR are restricted
                # user is in SR viewers
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                viewers=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset and SR are restricted
                # user is in SR editors
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                editors=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset and SR are restricted
                # user is SR author
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                author=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset and SR are restricted
                # user is in parent dataset admins
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                parent_dataset__admins=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            | Q(
                # parent dataset and SR are restricted
                # user is in parent dataset editors
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                parent_dataset__editors=request.user.id,
                visibility=VisibilityChoices.RESTRICTED,
            )
            # parent dataset is restricted but SR is public checks
            | Q(
                # parent dataset is restricted and SR public
                # user is in parent dataset editors
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                parent_dataset__editors=request.user.id,
                visibility=VisibilityChoices.PUBLIC,
            )
            | Q(
                # parent dataset is restricted and SR public
                # user is in parent dataset admins
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                parent_dataset__admins=request.user.id,
                visibility=VisibilityChoices.PUBLIC,
            )
            | Q(
                # parent dataset is restricted and SR public
                # user is in parent dataset viewers
                parent_dataset__visibility=VisibilityChoices.RESTRICTED,
                parent_dataset__viewers=request.user.id,
                visibility=VisibilityChoices.PUBLIC,
            ),
            parent_dataset__project__members=request.user.id,
            id=x.id,
        ).exists(),
    }

    # If `obj` is a scan report table|field|value, get the scan report
    # it belongs to and check the user has permission to view it.
    if sub_scan_report := SCAN_REPORT_QUERIES.get(type(obj)):
        sub_scan_report = sub_scan_report(obj)
        return checks.get(type(sub_scan_report))(sub_scan_report)

    # If `obj` is a dataset or scan report, check the user can view it.
    if permission_check := checks.get(type(obj)):
        return permission_check(obj)

    return False


def has_editorship(obj: Any, request: Request) -> bool:
    """Check the editorship permission on an object.

    Args:
        obj (Any): The object to check the permissions on.
        request (Request): The request with the User instance.

    Returns:
        bool: `True` if the request's user has permission, else `False`.
    """
    # Permission checks to perform
    checks = {
        Dataset: lambda x: Dataset.objects.filter(
            project__members__id=request.user.id, editors__id=request.user.id, id=x.id
        ).exists(),
        ScanReport: lambda x: ScanReport.objects.filter(
            Q(parent_dataset__editors__id=request.user.id)
            | Q(editors__id=request.user.id),
            parent_dataset__project__members__id=request.user.id,
            id=x.id,
        ).exists(),
    }

    # If `obj` is a scan report table|field|value, get the scan report
    # it belongs to and check the user has permission to edit it.
    if sub_scan_report := SCAN_REPORT_QUERIES.get(type(obj)):
        sub_scan_report = sub_scan_report(obj)
        return checks.get(type(sub_scan_report))(sub_scan_report)

    # If `obj` is a dataset or scan report, check the user can edit it.
    if permission_check := checks.get(type(obj)):
        return permission_check(obj)

    return False


def is_admin(obj: Any, request: Request) -> bool:
    """Check the admin permission on an object.

    Args:
        obj (Any): The object to check the permissions on.
        request (Request): The request with the User instance.

    Returns:
        bool: `True` if the request's user has permission, else `False`.
    """
    # Permission checks to perform
    checks = {
        Dataset: lambda x: Dataset.objects.filter(
            project__members__id=request.user.id, admins__id=request.user.id, id=x.id
        ).exists(),
        ScanReport: lambda x: ScanReport.objects.filter(
            Q(parent_dataset__admins__id=request.user.id)
            | Q(author__id=request.user.id),
            parent_dataset__project__members__id=request.user.id,
            id=x.id,
        ).exists(),
    }

    # If `obj` is a scan report table|field|value, get the scan report
    # it belongs to and check the user has permission to edit it.
    if sub_scan_report := SCAN_REPORT_QUERIES.get(type(obj)):
        sub_scan_report = sub_scan_report(obj)
        return checks.get(type(sub_scan_report))(sub_scan_report)

    # If `obj` is a dataset or scan report, check the user can edit it.
    if permission_check := checks.get(type(obj)):
        return permission_check(obj)

    return False


class CanViewProject(permissions.BasePermission):
    message = "You must be a member of this project to view its contents."

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if the User's ID is in the Project's members.
        """
        return obj.members.filter(id=request.user.id).exists()


class CanView(permissions.BasePermission):

    message = "You do not have permission to view this."

    def has_object_permission(self, request, view, obj):
        """
        Return `True` in any of the following cases:
            - the User is the `AZ_FUNCTION_USER`
            - the Object is 'RESTRICTED' and the User is an Object viewer
            - the Object is 'PUBLIC' and the User is a member of a Project
            that the Object is in.
        """

        if is_az_function_user(request.user):
            return True
        return has_viewership(obj, request)


class CanEdit(permissions.BasePermission):

    message = "You do not have permission to edit this."

    def has_object_permission(self, request, view, obj):
        """
        Return `True` in any of the following cases:
            - the User is the `AZ_FUNCTION_USER`
            - the User is an Object editor.
        """

        if is_az_function_user(request.user):
            return True
        return has_editorship(obj, request)


class CanAdmin(permissions.BasePermission):

    message = "You are not an admin of this."

    def has_object_permission(self, request, view, obj):
        """
        Return `True` in any of the following cases:
            - the User is the `AZ_FUNCTION_USER`
            - the User is an Object admin.
        """

        if is_az_function_user(request.user):
            return True
        return is_admin(obj, request)
