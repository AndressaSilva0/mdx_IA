"""
Django settings for mdx_project.
Evento: Mermãs Digitais | MDX 2026 • IFMA
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-mermas-digitais-mdx-2026-ifma-secret-key-!#$')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# Origens confiáveis para requisições HTTPS em produção (Render, PythonAnywhere, etc.)
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.pythonanywhere.com',
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]
if os.getenv('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS.extend(os.getenv('CSRF_TRUSTED_ORIGINS').split(','))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # App do Desafio MDX
    'game.apps.GameConfig',
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

ROOT_URLCONF = 'mdx_project.urls'

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
                'django.template.context_processors.media',
                'django.template.context_processors.static',
            ],
        },
    },
]

WSGI_APPLICATION = 'mdx_project.wsgi.application'

# Configuração de Banco de Dados (MySQL por padrão, compatível com PythonAnywhere)
# No PythonAnywhere, utilize o host: seu_usuario.mysql.pythonanywhere-services.com
DB_ENGINE = os.getenv('DB_ENGINE', 'mysql').lower()

if DB_ENGINE == 'sqlite' or os.getenv('USE_SQLITE', 'False').lower() in ('true', '1'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Garante driver PyMySQL
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'mdx_2026_db'),
            'USER': os.getenv('DB_USER', 'root'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': os.getenv('DB_HOST', '127.0.0.1'),
            'PORT': os.getenv('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# Password validation
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

# Internacionalização (Horário do Maranhão / IFMA)
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True

# Arquivos Estáticos e Mídia
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Suporte ao WhiteNoise para servir arquivos estáticos em produção (Render, Railway, etc.)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

