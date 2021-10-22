"""
Django settings for mcgm project.

Generated by 'django-admin startproject' using Django 2.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'v9e5c_$avdm58jt2g=tvgc$*34pj^z$vi8j8s*a_ghmr=+^!2='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

SHARED_APPS = [
    'tenant_schemas',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',
    'psqlextra',
    'departments',
    'common',
    'accounts',
    'crispy_forms',
    'bootstrap4',
    'floppyforms',
    'rest_framework',
    'rest_framework_gis'
]

TENANT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django.contrib.postgres',
    'psqlextra',
    'accounts',
    'swmadmin',
    'reports',
    'dashboard',
    'events',
    'health',
    'water',
    'fireservices', 
    'floppyforms',
    'crispy_forms',
    'bootstrap4',
]

INSTALLED_APPS = list(set(SHARED_APPS + TENANT_APPS))

MIDDLEWARE = [
    'tenant_schemas.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mcgm.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ os.path.join(BASE_DIR, 'templates') ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mcgm.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'psqlextra.backend',
        'NAME': 'mcgm_testing_sample',
        'USER': 'mcgm',
        'PASSWORD':'mcgm'
    }
}

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

POSTGRES_EXTRA_DB_BACKEND_BASE ='tenant_schemas.postgresql_backend'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

DATETIME_FORMAT = '%d-%m-%Y %H:%M:%S'

USE_I18N = True

USE_L10N = False 

#USE_TZ = True 

TIME_ZONE = 'Asia/Kolkata'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_DIRS=[
        os.path.join(BASE_DIR,'static'),
        ]

TENANT_MODEL = "departments.department"

DEFAULT_FILE_STORAGE = (
    'tenant_schemas.storage.TenantFileSystemStorage'
)

LOGOUT_REDIRECT_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
CRISPY_TEMPLATE_PACK = 'bootstrap4'
