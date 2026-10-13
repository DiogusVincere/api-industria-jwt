"""
Configurações do Django para o projeto somativa (API Indústria 4.0).

Tudo o que muda entre a máquina de desenvolvimento e o servidor vem de
variáveis de ambiente — ver .env.example na raiz.
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent


def _bool(valor, padrao=False):
    """Converte "True", "1", "sim"... em booleano; vazio devolve o padrão."""
    if valor is None or valor.strip() == "":
        return padrao
    return valor.strip().lower() in ("1", "true", "t", "yes", "y", "sim", "s")


def _lista(valor, padrao=""):
    """Converte "a,b, c" em ["a", "b", "c"]."""
    return [item.strip() for item in (valor or padrao).split(",") if item.strip()]


# SECRET_KEY: em produção defina a variável de ambiente SECRET_KEY.
# Sem ela, uma chave aleatória é gerada a cada inicialização — serve para
# desenvolver, mas invalida sessões e tokens JWT toda vez que o servidor reinicia
# (o SIMPLE_JWT assina os tokens com esta chave).
SECRET_KEY = os.environ.get("SECRET_KEY") or get_random_secret_key()

# DEBUG fica desligado por padrão; ligue com DEBUG=True só em desenvolvimento.
DEBUG = _bool(os.environ.get("DEBUG"), padrao=False)

# Lista separada por vírgula.
ALLOWED_HOSTS = _lista(os.environ.get("ALLOWED_HOSTS"), "localhost,127.0.0.1")

# CORS: por padrão libera qualquer origem. Para restringir, defina
# CORS_ALLOW_ALL_ORIGINS=False e CORS_ALLOWED_ORIGINS=https://meusite.com,...
CORS_ALLOW_ALL_ORIGINS = _bool(os.environ.get("CORS_ALLOW_ALL_ORIGINS"), padrao=True)
CORS_ALLOWED_ORIGINS = _lista(os.environ.get("CORS_ALLOWED_ORIGINS"))
CORS_ALLOW_CREDENTIALS = True


# Aplicações

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "djoser",
    "django_filters",
    "somativa_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "somativa.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "somativa.wsgi.application"


# Banco de dados (SQLite)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Validação de senha

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internacionalização

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# Arquivos estáticos e de mídia (fotos das máquinas)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Usuário customizado: o funcionário entra com o número de registro.
AUTH_USER_MODEL = "somativa_app.Funcionario"


# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}


# JWT

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}


# Djoser (cadastro de usuários e rotas JWT em /api/auth/)

DJOSER = {
    "LOGIN_FIELD": "numero_registro",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "USERNAME_CHANGED_EMAIL_CONFIRMATION": False,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": False,
    "SEND_CONFIRMATION_EMAIL": False,
    "SEND_ACTIVATION_EMAIL": False,
    "SET_USERNAME_RETYPE": False,
    "SET_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_URL": "password/reset/confirm/{uid}/{token}",
    "USERNAME_RESET_CONFIRM_URL": "username/reset/confirm/{uid}/{token}",
    "ACTIVATION_URL": "activate/{uid}/{token}",
    "SERIALIZERS": {
        "user_create": "somativa_app.serializers.FuncionarioCreateSerializer",
        "user": "somativa_app.serializers.FuncionarioSerializer",
        "current_user": "somativa_app.serializers.FuncionarioSerializer",
    },
}
