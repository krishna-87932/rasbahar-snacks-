import os
import logging
from django.http import HttpResponse, HttpResponseForbidden

logging.basicConfig(level=logging.INFO)

def setup_admin_view(request):
    token = request.GET.get('token')
    expected = os.environ.get('ADMIN_SETUP_TOKEN')
    if not expected or token != expected:
        return HttpResponseForbidden('Forbidden')

    username = os.environ.get('ADMIN_USERNAME')
    email = os.environ.get('ADMIN_EMAIL', '')
    password = os.environ.get('ADMIN_PASSWORD')
    if not username or not password:
        return HttpResponse('ADMIN_USERNAME and ADMIN_PASSWORD must be set in env vars', status=500)

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return HttpResponse(f'User {username} already exists')
        User.objects.create_superuser(username=username, email=email, password=password)
        return HttpResponse(f'Created admin user {username}')
    except Exception as e:
        logging.exception('Error creating admin')
        return HttpResponse(f'Error: {e}', status=500)
