from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<str:purpose>/', views.verify_otp_view, name='verify_otp'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/password/', views.change_password_view, name='change_password'),
    path('add-address/', views.add_address_view, name='add_address'),
    path('forget_password', views.forget_password, name="forget_password"),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('otp_verify/', views.forget_pass_otp_verify, name='forget_otp_verify'),
]
