"""
WSGI config for rasbahar_snacks project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import traceback
import logging

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rasbahar_snacks.settings')

# Configure minimal logging to a file in /tmp so we can inspect runtime issues on Vercel
LOG_PATH = os.environ.get('WSGI_LOG_PATH', '/tmp/rasbahar_wsgi.log')
logging.basicConfig(level=logging.INFO, filename=LOG_PATH, format='%(asctime)s %(levelname)s %(message)s')

application = get_wsgi_application()

def _run_startup_tasks():
    try:
        logging.info('Running startup migrations')
        call_command('migrate', interactive=False, verbosity=1)
        logging.info('Migrations completed successfully')
    except Exception as exc:
        msg = f'Error running migrations: {exc}\n{traceback.format_exc()}'
        logging.error(msg)
        # Also write to stderr so Vercel logs capture it
        print(msg)

    # Optional: create a superuser from environment variables if provided
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if admin_username and admin_password:
            logging.info('Ensuring admin user exists')
            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_superuser(username=admin_username, email=admin_email or '', password=admin_password)
                logging.info('Created admin user %s', admin_username)
            else:
                logging.info('Admin user %s already exists', admin_username)
    except Exception as exc:
        msg = f'Error creating admin user: {exc}\n{traceback.format_exc()}'
        logging.error(msg)
        print(msg)


try:
    _run_startup_tasks()
except Exception:
    # Prevent startup failure; errors are logged above
    logging.exception('Unhandled exception during startup tasks')

app = application