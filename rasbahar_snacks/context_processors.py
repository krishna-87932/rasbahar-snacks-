"""
Context processor to inject admin sidebar data into all dashboard templates.
"""
from orders.models import Order


def admin_sidebar_context(request):
    """Add pending order count to all templates for the sidebar badge."""
    if request.user.is_authenticated and request.user.is_staff:
        return {
            'pending_count': Order.objects.filter(status=Order.STATUS_PENDING).count(),
        }
    return {}
