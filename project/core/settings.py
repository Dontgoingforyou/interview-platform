import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from celery.schedules import crontab

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

_is_testing_env = os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules

SECRET_KEY = os.getenv('SECRET_KEY', 'test-secret-key')

# DEBUG по умолчанию False — явно задавать DEBUG=True в .env для локальной разработки
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Проверка, что не используется дефолтный SECRET_KEY вне локальной разработки и тестов
if SECRET_KEY == 'test-secret-key' and not DEBUG and not _is_testing_env:
    raise ValueError(
        "Использование дефолтного SECRET_KEY запрещено вне DEBUG-режима! "
        "Установите переменную окружения SECRET_KEY."
    )

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_TIMEZONE = 'Europe/Moscow'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_RETRY = True

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_RESULT_EXPIRES = 3600
# Fix for Celery 5.6 with Python 3.13
CELERY_BROKER_CHANNEL_ERROR_RETRY = True
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    'max_retries': 3,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.2,
}

# Таймауты
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_retries': 5,
    'interval_start': 0,
    'interval_step': 0.2,
    'interval_max': 0.5,
}

CELERY_BEAT_SCHEDULE = {
    'delete-stale-hidden-managers': {
        'task': 'managers.tasks.delete_stale_hidden_managers',
        'schedule': crontab(hour=3, minute=0),
    },
}

# Лимиты для загрузки файлов
# DATA_UPLOAD_MAX_MEMORY_SIZE — только для non-file POST данных (CSRF-токен и т.п.)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 МБ (non-file данные)
# FILE_UPLOAD_MAX_MEMORY_SIZE — порог, выше которого файл уходит во временный файл на диске
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024   # 10 МБ (файлы больше идут во временный файл)

LOG_FILE_INTERVIEWS = os.path.join(LOGS_DIR, 'interview_import.log')
LOG_FILE_INTERVIEWS_EXPORT = os.path.join(LOGS_DIR, 'interview_export.log')
LOG_FILE_INTERNS = os.path.join(LOGS_DIR, 'intern_import.log')
LOG_FILE_DEBTS = os.path.join(LOGS_DIR, 'debts_import.log')
LOG_FILE_OFFERS = os.path.join(LOGS_DIR, 'offers_import.log')
LOG_FILE_SAD_INTERN = os.path.join(LOGS_DIR, 'sad_intern_import.log')

# Логи для CRUD операций по приложениям
LOG_FILE_INTERVIEWS_CRUD = os.path.join(LOGS_DIR, 'interviews_crud.log')
LOG_FILE_INTERNS_CRUD = os.path.join(LOGS_DIR, 'interns_crud.log')
LOG_FILE_DEBTS_CRUD = os.path.join(LOGS_DIR, 'debts_crud.log')
LOG_FILE_OFFERS_CRUD = os.path.join(LOGS_DIR, 'offers_crud.log')
LOG_FILE_SAD_INTERN_CRUD = os.path.join(LOGS_DIR, 'sad_intern_crud.log')
LOG_FILE_MANAGERS_CRUD = os.path.join(LOGS_DIR, 'managers_crud.log')
LOG_FILE_EMPLOYEES_CRUD = os.path.join(LOGS_DIR, 'employees_crud.log')
LOG_FILE_DEVELOPERS_CRUD = os.path.join(LOGS_DIR, 'developers_crud.log')
LOG_FILE_DIRECTIONS_CRUD = os.path.join(LOGS_DIR, 'directions_crud.log')
LOG_FILE_COMPANIES_CRUD = os.path.join(LOGS_DIR, 'companies_crud.log')
LOG_FILE_KNOWLEDGE_BASE_CRUD = os.path.join(LOGS_DIR, 'knowledge_base_crud.log')
LOG_FILE_API_ACCESS = os.path.join(LOGS_DIR, 'api_access.log')
LOG_FILE_VECTOR_SEARCH = os.path.join(LOGS_DIR, 'vector_search.log')
LOG_FILE_INTERNS_PORTAL = os.path.join(LOGS_DIR, 'interns_portal.log')
LOG_FILE_TRANSCRIPTIONS = os.path.join(LOGS_DIR, 'transcriptions.log')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'info_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'info.log'),
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 3,
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'errors.log'),
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 3,
        },
        'interviews_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERVIEWS,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        'interviews_file_export': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERVIEWS_EXPORT,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        'interns_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERNS,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        'debts_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DEBTS,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        'offers_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_OFFERS,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        'sad_intern_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_SAD_INTERN,
            'formatter': 'verbose',
            'maxBytes': 5242880,  # 5MB
            'backupCount': 2,
        },
        # Handlers для CRUD операций
        'interviews_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERVIEWS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'interns_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERNS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'debts_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DEBTS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'offers_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_OFFERS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'sad_intern_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_SAD_INTERN_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'managers_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_MANAGERS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'employees_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_EMPLOYEES_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'developers_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DEVELOPERS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'directions_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_DIRECTIONS_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'companies_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_COMPANIES_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'knowledge_base_crud_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_KNOWLEDGE_BASE_CRUD,
            'formatter': 'verbose',
            'maxBytes': 10485760,
            'backupCount': 5,
        },
        'api_access_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_API_ACCESS,
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'vector_search_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_VECTOR_SEARCH,
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'interns_portal_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_INTERNS_PORTAL,
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'transcriptions_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_TRANSCRIPTIONS,
            'formatter': 'verbose',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['info_file', 'error_file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interview_import': {
            'handlers': ['interviews_file', 'info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interview_export': {
            'handlers': ['interviews_file_export', 'info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'intern_import': {
            'handlers': ['interns_file', 'info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'debts_import': {
            'handlers': ['debts_file', 'info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core.base_services': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'offers_import': {
            'handlers': ['offers_file', 'info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sad_intern_import': {
            'handlers': ['sad_intern_file', 'info_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interviews': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interns': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'debts': {
            'handlers': ['info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        # Логгеры для CRUD операций по моделям
        'interviews.interview': {
            'handlers': ['interviews_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interns.intern': {
            'handlers': ['interns_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'debts.debt': {
            'handlers': ['debts_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'offers.offer': {
            'handlers': ['offers_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'sad_intern.sadintern': {
            'handlers': ['sad_intern_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'managers': {
            'handlers': ['managers_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'employees': {
            'handlers': ['employees_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'developers': {
            'handlers': ['developers_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'directions.direction': {
            'handlers': ['directions_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'companies': {
            'handlers': ['companies_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'companies.company': {
            'handlers': ['companies_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'knowledge_base': {
            'handlers': ['knowledge_base_crud_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api_access': {
            'handlers': ['api_access_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'vector_search': {
            'handlers': ['vector_search_file', 'info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'interns_portal': {
            'handlers': ['interns_portal_file', 'info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'transcriptions': {
            'handlers': ['transcriptions_file', 'info_file', 'error_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Хосты берутся из ALLOWED_HOSTS. Без переменной остаётся только локальный запуск.
_allowed_hosts_env = os.getenv('ALLOWED_HOSTS', '').strip()
if _allowed_hosts_env:
    ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

_allow_localhost = os.getenv('ALLOW_LOCALHOST', '').strip().lower() in {'1', 'true', 'yes'}
if DEBUG or _allow_localhost:
    for _host in ('localhost', '127.0.0.1', '0.0.0.0'):
        if _host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(_host)


CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'http://localhost:82',
    'http://127.0.0.1:82',
]

# Яндекс Диск — legacy: транскрипция старых video_link
YANDEX_DISK_TOKEN = os.getenv('YA_TOKEN')
YANDEX_DISK_UPLOAD_DIR = os.getenv('YA_UPLOAD_DIR', 'interview_videos')

# S3 — загрузка видео
S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL', '').strip()
S3_REGION = os.getenv('S3_REGION', 'ru-central1').strip()
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID', '').strip()
S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY', '').strip()
S3_VIDEO_BUCKET = os.getenv('S3_VIDEO_BUCKET', 'interview-videos').strip()
S3_VIDEO_PREFIX = os.getenv('S3_VIDEO_PREFIX', '').strip()
S3_PRESIGNED_EXPIRES = int(os.getenv('S3_PRESIGNED_EXPIRES', '86400'))

if not DEBUG and not _is_testing_env:
    _missing_s3 = [
        name for name, val in (
            ('S3_ENDPOINT_URL', S3_ENDPOINT_URL),
            ('S3_ACCESS_KEY_ID', S3_ACCESS_KEY_ID),
            ('S3_SECRET_ACCESS_KEY', S3_SECRET_ACCESS_KEY),
            ('S3_VIDEO_BUCKET', S3_VIDEO_BUCKET),
        )
        if not val
    ]
    if _missing_s3:
        raise ValueError(
            'Для production задайте переменные S3: ' + ', '.join(_missing_s3)
        )

# Deepgram — транскрипция видеозаписей собеседований
DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY', '')
DEEPGRAM_PROJECT_ID = os.getenv('DEEPGRAM_PROJECT_ID', '')

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django_celery_beat',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',  # CORS support

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_vite',  # интеграция с Vite (React SPA)

    'core',
    'interviews',
    'accounts',
    'interns',
    'debts',
    'offers',
    'managers',
    'directions',
    'companies',
    'sad_intern',
    'employees',
    'developers',
    'knowledge_base_app',
    'interviews_database',
    'interns_portal',
    'transcriptions',
]
# Векторизация (pgvector): отключается через DISABLE_VECTOR=true в локальном Docker
if os.getenv('DISABLE_VECTOR', '').lower() not in ('true', '1', 'yes'):
    INSTALLED_APPS.append('vector_search')

# Django Debug Toolbar (только для разработки, не в тестах)
if DEBUG and not (os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules):
    INSTALLED_APPS.insert(0, 'debug_toolbar')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS должен быть перед CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.StudentRedirectMiddleware',
    'core.middleware.SessionRoleRepairMiddleware',
    'core.middleware.HROutstaffRedirectMiddleware',
    'core.middleware.MentorRedirectMiddleware',
    'core.middleware.ApiAccessLoggingMiddleware',
]

# Django Debug Toolbar middleware (только для разработки, не в тестах)
if DEBUG and not (os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules):
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.student_session',
                'core.context_processors.can_write',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    },
}

if 'test' in sys.argv or 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'test_db.sqlite3',
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

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# --- React / Vite ---
# django-vite: либо бандл из manifest (staticfiles/frontend/), либо скрипты с Vite dev (:5173).
# При DEBUG=True и dev_mode=True теги ведут на @vite/client — это работает только если страница
# открыта в паре с запущенным `npm run dev`. Через Nginx :82 без Vite получаются 404 на client/index.
# Поэтому dev_mode включается только явно (локально: runserver + Vite).
_use_vite_dev_server = DEBUG and os.getenv(
    'DJANGO_VITE_DEV', ''
).lower() in ('true', '1', 'yes')

DJANGO_VITE = {
    'default': {
        'dev_mode': _use_vite_dev_server,
        'dev_server_port': 5173,
        'manifest_path': BASE_DIR / 'staticfiles' / 'frontend' / '.vite' / 'manifest.json',
        'static_url_prefix': 'frontend/',
    }
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
# Временные видео портала студента — вне MEDIA_ROOT, nginx /media/ их не отдаёт.
PRIVATE_UPLOAD_ROOT = BASE_DIR / 'private_uploads'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Кэш — Redis (DB 1, чтобы не пересекаться с Celery на DB 0; пароль наследуется из REDIS_URL)
_redis_cache_url = os.getenv('REDIS_CACHE_URL', REDIS_URL.rsplit('/', 1)[0] + '/1')
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': _redis_cache_url,
        'TIMEOUT': 300,  # TTL по умолчанию: 5 минут
        'KEY_PREFIX': 'imp',
    }
}

# pytest / manage.py test: без Redis из .env (Celery update_state, Django cache, AsyncResult)
if _is_testing_env:
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

# REST Framework настройки
REST_FRAMEWORK = {
    # Аутентификация: сессия локального входа.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.KeycloakSessionAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # По умолчанию требуется аутентификация (можно переопределить в views)
    'DEFAULT_PERMISSION_CLASSES': [
        'accounts.permissions.IsKeycloakAuthenticated',
    ],
    # Пагинация
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    # Swagger/OpenAPI схема
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # Обработка исключений
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    # Формат дат
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'TIME_FORMAT': '%H:%M:%S',
    'DEFAULT_THROTTLE_CLASSES': [
        'core.throttling.ApiUserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'api_user': '1000/hour',
        'portal_upload': '10/hour',
        'spa_auth': '30/minute',
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Платформа собеседований API',
    'DESCRIPTION': (
        'API для управления студентами, собеседованиями, офферами и долгами.\n\n'
        '**Аутентификация:** сессионная кука после POST /api/auth/login/.\n'
        'Демо-учётки описаны в README.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    # Настройки безопасности в Swagger — документация доступна только авторизованным
    'SERVE_PERMISSIONS': ['accounts.permissions.IsKeycloakAuthenticated'],
    'SERVE_AUTHENTICATION': [
        'accounts.authentication.KeycloakSessionAuthentication',
    ],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'SessionAuth': {
                'type': 'apiKey',
                'in': 'cookie',
                'name': 'sessionid',
                'description': 'Сессия после локального входа.',
            },
        }
    },
    'SECURITY': [{'SessionAuth': []}],
    # Порядок и подписи разделов в Swagger UI (имена совпадают с tags в @extend_schema).
    # Тег «Векторный поиск» только если приложение vector_search в INSTALLED_APPS
    # (при DISABLE_VECTOR=true маршрутов /api/vector/ нет — пустой раздел вводил в заблуждение).
    'TAGS': [
        {'name': 'Документация API', 'description': 'Схема OpenAPI, Swagger UI, ReDoc'},
        {'name': 'Авторизация', 'description': 'Локальный вход демо-учётки'},
        {'name': 'Аналитика', 'description': 'Сводные метрики и дашборды'},
        {'name': 'Менеджеры', 'description': 'Учётные записи менеджеров и смежная аналитика'},
        {'name': 'Студенты', 'description': 'Учебные записи (API-префикс /interns/)'},
        {'name': 'Грустящие студенты', 'description': 'Список ожидания (API-префикс /sad-interns/)'},
        {'name': 'Портал студента', 'description': 'Личный кабинет студента'},
    ] + (
        [{'name': 'Векторный поиск', 'description': 'Семантический поиск по данным (только при подключённом приложении vector_search)'}]
        if 'vector_search' in INSTALLED_APPS
        else []
    ),
}

CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() == 'true'
CORS_ALLOWED_ORIGINS = [
    # HTTP только для локальной разработки
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Безопасность HTTPS (для production)
# Отключаем в тестах, чтобы избежать редиректов
is_testing = os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules
if not DEBUG and not is_testing:
    SECURE_SSL_REDIRECT = True
    # Указываем Django, что запросы приходят через HTTPS прокси (nginx)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # HSTS (HTTP Strict Transport Security) - защита от downgrade атак
    SECURE_HSTS_SECONDS = 31536000  # 1 год
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # Cookie security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = False  # False — JS должен читать куку для AJAX-запросов
    CSRF_COOKIE_SAMESITE = 'Lax'

    # Additional security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_HTTPONLY = False  # False — JS должен читать куку для AJAX-запросов
    CSRF_COOKIE_SAMESITE = 'Lax'

# Django Debug Toolbar настройки (только для разработки, не в тестах)
if DEBUG and not (os.getenv('DJANGO_TESTING') == '1' or 'test' in sys.argv or 'pytest' in sys.modules):
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
        '0.0.0.0',
    ]

    # Разрешаем показывать панель для Docker контейнеров
    import socket
    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[: ip.rfind(".")] + ".1" for ip in ips]

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_COLLAPSED': True,
        'HIDE_DJANGO_SQL': False,
    }

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv(
    'OPENAI_BASE_URL',
    'https://api.openai.com/v1',
).rstrip('/')

EMBEDDING_MODEL_NAME = os.getenv('EMBEDDING_MODEL_NAME', 'text-embedding-3-small')
EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', '1536'))

EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '100'))
SEMANTIC_SEARCH_TOP_K = int(os.getenv('SEMANTIC_SEARCH_TOP_K', '10'))
SEMANTIC_SEARCH_MIN_SCORE = float(os.getenv('SEMANTIC_SEARCH_MIN_SCORE', '0.3'))
