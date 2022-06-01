import os
from pathlib import Path
from split_settings.tools import include


BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', False) == 'True'
ALLOWED_HOSTS = ['127.0.0.1']
INTERNAL_IPS = ['127.0.0.1']
LOCALE_PATHS = ['movies/locale']
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:8080", ]

include(
    'components/logger.py',  # LOGGING
    'components/apps.py',  # Application definition
    'components/middleware.py',  # Middleware
    'components/templates.py',  # Templates
    'components/database.py',  # Database
    'components/auth.py',  # Auth
    'components/i18n.py',  # Internationalization
)
