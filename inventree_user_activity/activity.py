"""Aggregate InvenTree activity records for a single user."""

from django.contrib.auth import get_user_model

User = get_user_model()


def _owner_filter(user):
    """Return the set of Owner records (user + groups) matching a user."""
    from users.models import Owner

    return Owner.get_owners_matching_user(user)


def gather_user_activity(user: User) -> dict:
    """Collect all activity records associated with the given user.

    Returns a dict of querysets/lists, grouped by category, ready to be
    passed into a report template or serialized for the UI panel.
    """
    from build.models import Build
    from common.models import Attachment, NotesImage
    from order.models import PurchaseOrder, SalesOrder, ReturnOrder
    from part.models import Part
    from stock.models import StockItemTracking

    owners = _owner_filter(user)

    return {
        'stock_tracking': StockItemTracking.objects.filter(user=user).order_by(
            '-date'
        ),
        'builds_issued': Build.objects.filter(issued_by=user).order_by(
            '-creation_date'
        ),
        'builds_responsible': Build.objects.filter(
            responsible__in=owners
        ).order_by('-creation_date'),
        'purchase_orders_created': PurchaseOrder.objects.filter(
            created_by=user
        ).order_by('-creation_date'),
        'purchase_orders_responsible': PurchaseOrder.objects.filter(
            responsible__in=owners
        ).order_by('-creation_date'),
        'sales_orders_created': SalesOrder.objects.filter(
            created_by=user
        ).order_by('-creation_date'),
        'sales_orders_responsible': SalesOrder.objects.filter(
            responsible__in=owners
        ).order_by('-creation_date'),
        'return_orders_created': ReturnOrder.objects.filter(
            created_by=user
        ).order_by('-creation_date'),
        'parts_created': Part.objects.filter(creation_user=user).order_by(
            '-creation_date'
        ),
        'attachments': Attachment.objects.filter(upload_user=user).order_by(
            '-upload_date'
        ),
        'notes_images': NotesImage.objects.filter(user=user).order_by('-date'),
    }


def summarize_user_activity(user: User) -> dict:
    """Return counts only, suitable for a lightweight UI panel summary."""
    data = gather_user_activity(user)
    return {key: queryset.count() for key, queryset in data.items()}
