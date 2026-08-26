"""Render the user activity report to PDF using WeasyPrint."""

from django.template.loader import render_to_string

from weasyprint import HTML

from .activity import gather_user_activity


def render_user_activity_pdf(user) -> bytes:
    """Render a PDF report of a user's activity across InvenTree."""
    context = {'target_user': user, 'activity': gather_user_activity(user)}

    html_string = render_to_string(
        'inventree_user_activity/report.html', context
    )

    return HTML(string=html_string).write_pdf()
