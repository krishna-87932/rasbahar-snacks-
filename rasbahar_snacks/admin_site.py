"""
Custom Admin Site Configuration
Provides enhanced dashboard and branding for the admin panel
"""
from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.urls import path


class RasbaharAdminSite(AdminSite):
    site_header = "🍔 Rasbahar Snacks - Admin Dashboard"
    site_title = "Rasbahar Admin"
    index_title = "Dashboard"

    def get_urls(self):
        from orders import dashboard_views

        urls = super().get_urls()
        original_index = self.index

        # Remove the default index URL (only URLPattern objects have .name)
        urls = [u for u in urls if getattr(u, 'name', None) != 'index']

        custom_urls = [
            # Dashboard
            path('', self.admin_view(dashboard_views.admin_dashboard), name='index'),
            path('dashboard/', self.admin_view(dashboard_views.admin_dashboard), name='admin_dashboard'),

            # Orders
            path('dashboard/orders/', self.admin_view(dashboard_views.orders_dashboard), name='orders_dashboard'),
            path('dashboard/orders/<int:order_id>/detail/', self.admin_view(dashboard_views.order_detail_api), name='order_detail_api'),
            path('dashboard/orders/<int:order_id>/status/', self.admin_view(dashboard_views.update_order_status_api), name='update_order_status_api'),

            # Menu Items
            path('dashboard/menu/', self.admin_view(dashboard_views.menu_dashboard), name='menu_dashboard'),
            path('dashboard/menu/add/', self.admin_view(dashboard_views.add_menu_item), name='add_menu_item'),
            path('dashboard/menu/<int:item_id>/detail/', self.admin_view(dashboard_views.menu_item_detail_api), name='menu_item_detail_api'),
            path('dashboard/menu/<int:item_id>/edit/', self.admin_view(dashboard_views.edit_menu_item), name='edit_menu_item'),
            path('dashboard/menu/<int:item_id>/delete/', self.admin_view(dashboard_views.delete_menu_item), name='delete_menu_item'),
            path('dashboard/menu/<int:item_id>/toggle/', self.admin_view(dashboard_views.toggle_menu_item), name='toggle_menu_item'),

            # Categories
            path('dashboard/categories/', self.admin_view(dashboard_views.categories_dashboard), name='categories_dashboard'),
            path('dashboard/categories/add/', self.admin_view(dashboard_views.add_category), name='add_category'),
            path('dashboard/categories/<int:cat_id>/detail/', self.admin_view(dashboard_views.category_detail_api), name='category_detail_api'),
            path('dashboard/categories/<int:cat_id>/edit/', self.admin_view(dashboard_views.edit_category), name='edit_category'),
            path('dashboard/categories/<int:cat_id>/delete/', self.admin_view(dashboard_views.delete_category), name='delete_category'),

            # Users
            path('dashboard/users/', self.admin_view(dashboard_views.users_dashboard), name='users_dashboard'),
            path('dashboard/users/<int:user_id>/detail/', self.admin_view(dashboard_views.user_detail_api), name='user_detail_api'),
            path('dashboard/users/<int:user_id>/toggle/', self.admin_view(dashboard_views.toggle_user_status), name='toggle_user_status'),

            # Original Django admin models page
            path('models/', self.admin_view(original_index), name='app_list'),
        ]
        return custom_urls + urls


class RasbaharAdminConfig(AdminConfig):
    """Custom admin config that disables autodiscovery to prevent circular imports"""
    def ready(self):
        # Skip the default autodiscovery
        # We'll manually register models in each app's admin.py using the custom admin_site
        pass


# Create instance
admin_site = RasbaharAdminSite(name='admin')
