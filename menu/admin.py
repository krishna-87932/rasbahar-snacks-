from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, MenuItem, AddOn
from rasbahar_snacks.admin_site import admin_site


@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon_display', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    
    def icon_display(self, obj):
        """Display icon"""
        return format_html('<span style="font-size: 20px;">{}</span>', obj.icon) if obj.icon else '-'
    icon_display.short_description = 'Icon'


@admin.register(MenuItem, site=admin_site)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_display', 'is_available', 'is_featured', 'veg_badge', 'image_preview')
    list_filter = ('category', 'is_available', 'is_featured', 'is_veg')
    list_editable = ('is_available', 'is_featured')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('image_preview_large', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Item Info', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'is_available', 'is_featured', 'is_veg')
        }),
        ('Image', {
            'fields': ('image', 'image_preview_large'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def price_display(self, obj):
        """Display price with currency"""
        return format_html(
            '<span style="font-weight: bold; color: #28a745;">Rs. {}</span>',
            obj.price
        )
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'
    
    def veg_badge(self, obj):
        """Display veg/non-veg status"""
        if obj.is_veg:
            return mark_safe(
                '<span style="background-color: #90EE90; color: black; padding: 5px 10px; border-radius: 3px;">🟢 Veg</span>'
            )
        else:
            return mark_safe(
                '<span style="background-color: #FFB6C6; color: black; padding: 5px 10px; border-radius: 3px;">🔴 Non-Veg</span>'
            )
    veg_badge.short_description = 'Type'
    veg_badge.admin_order_field = 'is_veg'
    
    def image_preview(self, obj):
        """Display small image preview in list"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image'
    
    def image_preview_large(self, obj):
        """Display large image preview in detail view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="300" style="border-radius: 10px; max-height: 400px; object-fit: cover;" />',
                obj.image.url
            )
        return 'No image uploaded'
    image_preview_large.short_description = 'Image Preview'


@admin.register(AddOn, site=admin_site)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_display', 'is_available', 'is_veg', 'linked_items_count', 'image_preview')
    list_filter = ('is_available', 'is_veg')
    list_editable = ('is_available',)
    search_fields = ('name',)
    filter_horizontal = ('menu_items',)
    readonly_fields = ('image_preview_large', 'created_at', 'updated_at')

    fieldsets = (
        ('Add-On Info', {
            'fields': ('name', 'price', 'is_available', 'is_veg')
        }),
        ('Linked Menu Items', {
            'fields': ('menu_items',),
            'description': 'Select which menu items this add-on should be suggested for.'
        }),
        ('Image', {
            'fields': ('image', 'image_preview_large'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        return format_html('<span style="font-weight: bold; color: #28a745;">₹{}</span>', obj.price)
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'price'

    def linked_items_count(self, obj):
        count = obj.menu_items.count()
        return format_html('<span style="font-weight: 600;">{} items</span>', count)
    linked_items_count.short_description = 'Linked Items'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 6px; object-fit: cover;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Image'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="200" style="border-radius: 10px; max-height: 300px; object-fit: cover;" />',
                obj.image.url
            )
        return 'No image uploaded'
    image_preview_large.short_description = 'Image Preview'
