from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/addon/<int:cart_item_id>/', views.add_addon_to_cart, name='add_addon_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart, name='update_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/<uuid:order_id>/', views.order_detail_view, name='order_detail'),
    path('orders/<uuid:order_id>/update-status/', views.update_order_status, name='update_status'),
]
