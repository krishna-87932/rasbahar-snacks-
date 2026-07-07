from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Cart, CartItem, Order, OrderItem
from rasbahar_snacks.admin_site import admin_site


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('item_name', 'item_price', 'quantity', 'subtotal')
    readonly_fields = ('item_name', 'item_price', 'quantity', 'subtotal')
    
    def subtotal(self, obj):
        """Calculate and display subtotal"""
        if obj.item_price and obj.quantity:
            return f"Rs. {obj.item_price * obj.quantity}"
        return "-"
    subtotal.short_description = "Subtotal"


def mark_as_preparing(modeladmin, request, queryset):
    """Bulk action to mark orders as preparing"""
    updated = queryset.update(status=Order.STATUS_PREPARING)
    modeladmin.message_user(request, f"{updated} order(s) marked as preparing.")
mark_as_preparing.short_description = "Mark selected as Preparing"


def mark_as_ready(modeladmin, request, queryset):
    """Bulk action to mark orders as ready"""
    updated = queryset.update(status=Order.STATUS_READY)
    modeladmin.message_user(request, f"{updated} order(s) marked as ready.")
mark_as_ready.short_description = "Mark selected as Ready"


def mark_as_out_for_delivery(modeladmin, request, queryset):
    """Bulk action to mark orders as out for delivery"""
    updated = queryset.update(status=Order.STATUS_OUT_FOR_DELIVERY)
    modeladmin.message_user(request, f"{updated} order(s) marked as out for delivery.")
mark_as_out_for_delivery.short_description = "Mark selected as Out for Delivery"


def mark_as_delivered(modeladmin, request, queryset):
    """Bulk action to mark orders as delivered"""
    updated = queryset.update(status=Order.STATUS_DELIVERED)
    modeladmin.message_user(request, f"{updated} order(s) marked as delivered.")
mark_as_delivered.short_description = "Mark selected as Delivered"


@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'user_name', 'status', 'total', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'payment_status', 'created_at')
    list_editable = ('status',)
    search_fields = ('user__name', 'user__phone_number', 'order_id')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'subtotal_display', 'total_display_full')
    date_hierarchy = 'created_at'
    actions = [mark_as_preparing, mark_as_ready, mark_as_out_for_delivery, mark_as_delivered]
    
    fieldsets = (
        ('Order Info', {
            'fields': ('order_id', 'user', 'created_at', 'updated_at')
        }),
        ('Status & Payment', {
            'fields': ('status', 'payment_method', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal_display', 'delivery_charge', 'discount', 'total_display_full'),
            'classes': ('collapse',)
        }),
        ('Delivery', {
            'fields': ('delivery_address', 'delivery_notes', 'estimated_delivery')
        }),
    )
    inlines = [OrderItemInline]

    def short_id(self, obj):
        """Display short order ID"""
        return obj.short_id
    short_id.short_description = 'Order ID'
    short_id.admin_order_field = 'order_id'
    
    def user_name(self, obj):
        """Display user name"""
        return obj.user.name
    user_name.short_description = 'Customer'
    user_name.admin_order_field = 'user__name'
    
    def total_display_full(self, obj):
        """Display full total breakdown"""
        return format_html(
            '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">'
            '<p>Subtotal: <strong>Rs. {}</strong></p>'
            '<p>Delivery: <strong>Rs. {}</strong></p>'
            '<p>Discount: <strong>Rs. {}</strong></p>'
            '<p style="border-top: 1px solid #ddd; margin-top: 10px; padding-top: 10px;">'
            'Total: <strong>Rs. {}</strong></p>'
            '</div>',
            obj.subtotal, obj.delivery_charge, obj.discount, obj.total
        )
    total_display_full.short_description = 'Total Amount'
    
    def subtotal_display(self, obj):
        """Display subtotal breakdown"""
        return format_html(
            '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px;">'
            '<p>Subtotal: <strong>Rs. {}</strong></p>'
            '<p>Delivery: <strong>Rs. {}</strong></p>'
            '<p>Discount: <strong>Rs. {}</strong></p>'
            '<p style="border-top: 1px solid #ddd; margin-top: 10px; padding-top: 10px;">'
            'Total: <strong>Rs. {}</strong></p>'
            '</div>',
            obj.subtotal, obj.delivery_charge, obj.discount, obj.total
        )
    subtotal_display.short_description = 'Price Breakdown'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('user').prefetch_related('order_items')
    
    def changelist_view(self, request, extra_context=None):
        """Add summary statistics to list view"""
        extra_context = extra_context or {}
        
        # Get statistics
        today = timezone.now().date()
        today_orders = Order.objects.filter(created_at__date=today)
        
        extra_context['summary'] = {
            'total_orders': Order.objects.count(),
            'today_orders': today_orders.count(),
            'pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
            'preparing_orders': Order.objects.filter(status=Order.STATUS_PREPARING).count(),
            'ready_orders': Order.objects.filter(status=Order.STATUS_READY).count(),
            'out_for_delivery': Order.objects.filter(status=Order.STATUS_OUT_FOR_DELIVERY).count(),
            'delivered_today': today_orders.filter(status=Order.STATUS_DELIVERED).count(),
            'total_revenue': Order.objects.filter(status=Order.STATUS_DELIVERED).aggregate(Sum('total'))['total__sum'] or 0,
            'today_revenue': today_orders.filter(status=Order.STATUS_DELIVERED).aggregate(Sum('total'))['total__sum'] or 0,
        }
        
        return super().changelist_view(request, extra_context)
