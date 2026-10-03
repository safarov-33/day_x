from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent




DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY when DJANGO_DEBUG=0.")
    SECRET_KEY = "django-insecure-local-development-only-change-before-deployment"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
CSRF_FAILURE_VIEW = "main.error_views.csrf_failure"



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'main.middleware.DefaultLanguageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

AUTH_USER_MODEL = "main.User"




TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]



LANGUAGE_CODE = 'en'
LANGUAGES = [('ru', 'Русский'), ('en', 'English'), ('tg', 'Тоҷикӣ')]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LANGUAGE_COOKIE_SAMESITE = 'Lax'

TIME_ZONE = 'Asia/Dushanbe'

USE_I18N = True

USE_TZ = True



STATIC_URL = 'static/'



MAILERS = {
    'default': {
        'BACKEND': os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"),
        'OPTIONS': {
            'host': os.environ.get("DJANGO_EMAIL_HOST", "localhost"),
            'port': int(os.environ.get("DJANGO_EMAIL_PORT", "587")),
            'username': os.environ.get("DJANGO_EMAIL_USER", ""),
            'password': os.environ.get("DJANGO_EMAIL_PASSWORD", ""),
            'use_tls': os.environ.get("DJANGO_EMAIL_TLS", "1") == "1",
        },
    },
}
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_FROM_EMAIL", "qarz@localhost")
