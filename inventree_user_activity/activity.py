"""Aggregate InvenTree activity records for a single user."""

from django.contrib.auth import get_user_model

User = get_user_model()


def _owner_filter(user):
    """Return the set of Owner records (user + groups) matching a user."""
    from users.models import Owner

    return Owner.get_owners_matching_user(user)


class _StockHistory:
    """A user's stock history, as uniform rows from either history backend.

    Behaves enough like a queryset for the report template and the summary
    (count(), truthiness, iteration), but yields plain dicts with the keys
    'date', 'item', 'type' and 'notes' whichever model the rows come from.
    """

    def __init__(self, queryset, to_row):
        self._queryset = queryset
        self._to_row = to_row

    def count(self) -> int:
        return self._queryset.count()

    def __bool__(self) -> bool:
        return self._queryset.exists()

    def __iter__(self):
        return (self._to_row(entry) for entry in self._queryset)


def _tracking_row(entry) -> dict:
    """Row for a legacy StockItemTracking entry (InvenTree < 1.7)."""
    return {
        'date': entry.date,
        'item': str(entry.item),
        'type': str(entry.label()),
        'notes': entry.notes or '',
    }


def _audit_row(entry) -> dict:
    """Row for an audit log entry recorded against a stock item (InvenTree >= 1.7)."""
    return {
        'date': entry.timestamp,
        'item': entry.object_repr,
        # Named stock events ("Stock item created", "Location changed", ...) carry
        # a label; plain edits and deletions only have the generic action.
        'type': entry.event_label or str(entry.get_action_display()).capitalize(),
        'notes': entry.notes or '',
    }


def _stock_history(user) -> _StockHistory:
    """Return the stock history recorded for a user.

    InvenTree 1.7.0 removed the StockItemTracking model: stock history (including
    every pre-existing tracking entry, migrated by stock migration 0129) now
    lives in the global audit log. Older releases only have StockItemTracking.
    """
    try:
        from stock.models import StockItemTracking
    except ImportError:
        StockItemTracking = None

    if StockItemTracking is not None:
        return _StockHistory(
            StockItemTracking.objects.filter(user=user).order_by('-date'),
            _tracking_row,
        )

    from django.contrib.contenttypes.models import ContentType

    from audit.models import AuditLogEntry
    from stock.models import StockItem

    return _StockHistory(
        AuditLogEntry.objects.filter(
            actor=user, content_type=ContentType.objects.get_for_model(StockItem)
        )
        .select_related('content_type')
        .order_by('-timestamp'),
        _audit_row,
    )


def gather_user_activity(user: User) -> dict:
    """Collect all activity records associated with the given user.

    Returns a dict of querysets/lists, grouped by category, ready to be
    passed into a report template or serialized for the UI panel.
    """
    from build.models import Build
    from common.models import Attachment, NotesImage
    from order.models import PurchaseOrder, SalesOrder, ReturnOrder
    from part.models import Part

    owners = _owner_filter(user)

    return {
        'stock_tracking': _stock_history(user),
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


def _serialize_stock_tracking(row):
    # Already a plain dict - see _StockHistory
    return row


def _serialize_build(build):
    return {
        'reference': build.reference,
        'part': str(build.part),
        'status': build.status_text,
        'creation_date': build.creation_date,
    }


def _serialize_order(order):
    return {
        'reference': order.reference,
        'status': order.status_text,
        'creation_date': order.creation_date,
    }


def _serialize_purchase_order(order):
    data = _serialize_order(order)
    data['supplier'] = str(order.supplier) if order.supplier else None
    return data


def _serialize_sales_or_return_order(order):
    data = _serialize_order(order)
    data['customer'] = str(order.customer) if order.customer else None
    return data


def _serialize_part(part):
    return {'IPN': part.IPN, 'name': part.name, 'creation_date': part.creation_date}


def _serialize_attachment(attachment):
    return {
        'file': str(attachment.attachment) if attachment.attachment else None,
        'comment': attachment.comment,
        'upload_date': attachment.upload_date,
    }


def _serialize_notes_image(image):
    return {
        'image': str(image.image) if image.image else None,
        'date': image.date,
    }


_SERIALIZERS = {
    'stock_tracking': _serialize_stock_tracking,
    'builds_issued': _serialize_build,
    'builds_responsible': _serialize_build,
    'purchase_orders_created': _serialize_purchase_order,
    'purchase_orders_responsible': _serialize_purchase_order,
    'sales_orders_created': _serialize_sales_or_return_order,
    'sales_orders_responsible': _serialize_sales_or_return_order,
    'return_orders_created': _serialize_sales_or_return_order,
    'parts_created': _serialize_part,
    'attachments': _serialize_attachment,
    'notes_images': _serialize_notes_image,
}


def serialize_user_activity(user: User) -> dict:
    """Return the full activity dataset as plain JSON-serializable records."""
    data = gather_user_activity(user)
    return {
        key: [_SERIALIZERS[key](record) for record in queryset]
        for key, queryset in data.items()
    }
