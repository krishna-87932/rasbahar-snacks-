from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count
from .models import User, OTPRecord
from rasbahar_snacks.admin_site import admin_site


@admin.register(User, site=admin_site)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'name', 'email', 'active_badge', 'staff_badge', 'orders_count', 'date_joined_display')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    search_fields = ('phone_number', 'name', 'email')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login', 'profile_picture_preview')
    
    fieldsets = (
        ('Login Info', {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('name', 'email', 'address', 'profile_picture', 'profile_picture_preview')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('date_joined', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'email', 'password1', 'password2'),
        }),
    )
    
    def active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return mark_safe(
                '<span style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 3px;">✓ Active</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 3px;">✗ Inactive</span>'
            )
    active_badge.short_description = 'Status'
    active_badge.admin_order_field = 'is_active'
    
    def staff_badge(self, obj):
        """Display staff status"""
        if obj.is_staff:
            return mark_safe(
                '<span style="background-color: #0066cc; color: white; padding: 5px 10px; border-radius: 3px;">👨 Staff</span>'
            )
        return '-'
    staff_badge.short_description = 'Role'
    staff_badge.admin_order_field = 'is_staff'
    
    def orders_count(self, obj):
        """Display number of orders"""
        count = obj.orders.count()
        return format_html(
            '<span style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 3px;">{} Orders</span>',
            count
        )
    orders_count.short_description = 'Orders'
    
    def date_joined_display(self, obj):
        """Display date joined in better format"""
        return obj.date_joined.strftime('%d %b %Y')
    date_joined_display.short_description = 'Joined'
    date_joined_display.admin_order_field = 'date_joined'
    
    def profile_picture_preview(self, obj):
        """Display profile picture preview"""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="200" style="border-radius: 10px; max-height: 300px; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return 'No profile picture'
    profile_picture_preview.short_description = 'Profile Picture'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).prefetch_related('orders')


@admin.register(OTPRecord, site=admin_site)
class OTPRecordAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'purpose_badge', 'otp_display', 'is_used_badge', 'created_at_display', 'expires_at_display')
    list_filter = ('purpose', 'is_used', 'created_at')
    search_fields = ('phone_number',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def purpose_badge(self, obj):
        """Display purpose as badge"""
        colors = {
            'registration': '#17a2b8',
            'login': '#0066cc',
            'password_reset': '#fd7e14',
            'verification': '#28a745',
        }
        color = colors.get(obj.purpose, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_purpose_display()
        )
    purpose_badge.short_description = 'Purpose'
    purpose_badge.admin_order_field = 'purpose'
    
    def otp_display(self, obj):
        """Display OTP with masking"""
        return format_html(
            '<span style="font-weight: bold; font-family: monospace; letter-spacing: 2px;">{}</span>',
            obj.otp
        )
    otp_display.short_description = 'OTP'
    
    def is_used_badge(self, obj):
        """Display used status"""
        if obj.is_used:
            return mark_safe(
                '<span style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 3px;">✓ Used</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 3px;">⏳ Pending</span>'
            )
    is_used_badge.short_description = 'Status'
    is_used_badge.admin_order_field = 'is_used'
    
    def created_at_display(self, obj):
        """Display creation time"""
        return obj.created_at.strftime('%d %b %Y, %I:%M %p')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'
    
    def expires_at_display(self, obj):
        """Display expiry time"""
        return obj.expires_at.strftime('%d %b %Y, %I:%M %p')
    expires_at_display.short_description = 'Expires'
    expires_at_display.admin_order_field = 'expires_at'
