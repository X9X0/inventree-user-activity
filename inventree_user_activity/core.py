"""Plugin definition: comprehensive activity report for a specific user."""

from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.urls import path

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, UrlsMixin, UserInterfaceMixin

from .activity import summarize_user_activity
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

    def get_ui_panels(self, request, context, **kwargs):
        """Add an 'Activity Report' panel to the User detail page."""
        context = context or {}

        if context.get('target_model') != 'user':
            return []

        target_id = context.get('target_id')
        try:
            target_user = User.objects.get(pk=target_id)
        except (User.DoesNotExist, TypeError, ValueError):
            return []

        if not self._can_view(request, target_user):
            return []

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
                'pdf_url': f'{self.base_url}report/{target_user.pk}/pdf/',
            },
        }]

    def view_report_pdf(self, request, user_id):
        """Serve the generated PDF activity report for the given user."""
        try:
            target_user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError):
            return HttpResponseNotFound('User not found')

        if not self._can_view(request, target_user):
            return HttpResponseForbidden(
                'You do not have permission to view this report'
            )

        pdf_bytes = render_user_activity_pdf(target_user)

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        filename = f'activity_report_{target_user.username}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def setup_urls(self):
        """Custom URL endpoints exposed by this plugin."""
        return [
            path(
                'report/<int:user_id>/pdf/',
                self.view_report_pdf,
                name='user-activity-report-pdf',
            )
        ]
