from django.urls import path
from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('menu/', views.menu_view, name='menu'),
    path('menu/<slug:slug>/', views.item_detail_view, name='item_detail'),
]
