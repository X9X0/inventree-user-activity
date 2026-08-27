"""Plugin definition: comprehensive activity report for a specific user."""

from django.contrib.auth import get_user_model
from django.core.serializers.json import DjangoJSONEncoder
from django.http import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseNotFound,
    JsonResponse,
)
from django.urls import path

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, UrlsMixin, UserInterfaceMixin

from .activity import serialize_user_activity, summarize_user_activity
from .pdf import render_user_activity_pdf

User = get_user_model()


class UserActivityReportPlugin(AppMixin, UrlsMixin, UserInterfaceMixin, InvenTreePlugin):
    """Generates a comprehensive activity report for a specific user."""

    NAME = 'UserActivityReport'
    SLUG = 'useractivityreport'
    TITLE = 'User Activity Report'
    DESCRIPTION = (
        'Generates a comprehensive report of stock, order, part and '
        'attachment activity for a specific user'
    )
    VERSION = '0.1.0'
    AUTHOR = 'X9X0'

    def _can_view(self, request, target_user) -> bool:
        """Only staff/superusers may view another user's activity; a user may view their own."""
        if request.user.is_staff or request.user.is_superuser:
            return True
        return request.user.pk == target_user.pk

    def _resolve_target_user(self, request, user_id):
        """Look up the target user and check view permission.

        Returns (user, None) on success, or (None, error_response) on failure.
        """
        try:
            target_user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, TypeError, ValueError):
            return None, HttpResponseNotFound('User not found')

        if not self._can_view(request, target_user):
            return None, HttpResponseForbidden(
                'You do not have permission to view this report'
            )

        return target_user, None

    def get_ui_panels(self, request, context, **kwargs):
        """Add an 'Activity Report' panel to the User detail page."""
        context = context or {}

        if context.get('target_model') != 'user':
            return []

        target_id = context.get('target_id')
        target_user, error = self._resolve_target_user(request, target_id)
        if error:
            return []

        base = f'/{self.base_url.lstrip("/")}report/{target_user.pk}'

        return [{
            'key': 'user-activity-report',
            'title': 'Activity Report',
            'icon': 'ti:report-analytics:outline',
            'source': self.plugin_static_file(
                'activity_panel.js:renderActivityPanel'
            ),
            'context': {
                'user_id': target_user.pk,
                'summary': summarize_user_activity(target_user),
                'pdf_url': f'{base}/pdf/',
                'data_url': f'{base}/data/',
            },
        }]

    def view_report_pdf(self, request, user_id):
        """Serve the generated PDF activity report for the given user."""
        target_user, error = self._resolve_target_user(request, user_id)
        if error:
            return error

        pdf_bytes = render_user_activity_pdf(target_user)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'activity_report_{target_user.username}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def view_report_data(self, request, user_id):
        """Serve the full activity dataset as JSON, for in-page browsing."""
        target_user, error = self._resolve_target_user(request, user_id)
        if error:
            return error

        data = serialize_user_activity(target_user)
        return JsonResponse(data, encoder=DjangoJSONEncoder)

    def setup_urls(self):
        """Custom URL endpoints exposed by this plugin."""
        return [
            path(
                'report/<int:user_id>/pdf/',
                self.view_report_pdf,
                name='user-activity-report-pdf',
            ),
            path(
                'report/<int:user_id>/data/',
                self.view_report_data,
                name='user-activity-report-data',
            ),
        ]
