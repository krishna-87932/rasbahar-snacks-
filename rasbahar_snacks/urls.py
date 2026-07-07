from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin_site import admin_site
from .setup_admin import setup_admin_view

urlpatterns = [
    path('admin/', admin_site.urls),
    path('setup-admin/', setup_admin_view, name='setup-admin'),
    path('', include('menu.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('orders.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
