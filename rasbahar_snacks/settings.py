from pathlib import Path
import os
from tempfile import gettempdir

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-rasbahar-snacks-change-in-production-xyz123'

DEBUG = True

# ALLOWED_HOSTS = ['rasbaharsnacks123.pythonanywhere.com', 'localhost', '127.0.0.1','192.168.43.8','0.0.0.0']
ALLOWED_HOSTS = ['*']  # Use specific hosts in production

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Local apps
    'accounts',
    'menu',
    'orders',

    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rasbahar_snacks.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'rasbahar_snacks.context_processors.admin_sidebar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'rasbahar_snacks.wsgi.application'

DB_PATH = os.environ.get('DB_PATH', str(Path(gettempdir()) / 'rasbahar_snacks.sqlite3'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DB_PATH,
    }
}
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'postgres',
#         'USER': 'postgres',
#         'PASSWORD': 'rasbahar123',
#         'HOST': 'db.mkmjndmevjiqxtgbfoon.supabase.co',
#         'PORT': '5432',
#     }
# }
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'menu:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# OTP Settings
OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6

# Restaurant Location & Delivery Radius
RESTAURANT_LAT = 18.5732323836383
RESTAURANT_LNG = 73.75629201112027
MAX_DELIVERY_RADIUS_KM = 10  # Maximum delivery distance in kilometers

# Email backend (console for dev)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'matrix202440@gmail.com'
EMAIL_HOST_PASSWORD = 'xbvdtriqmaptftni'

# WhiteNoise settings for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



