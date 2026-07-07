from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .admin_site import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('menu.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('orders.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
