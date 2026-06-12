import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# Puxa a chave do Railway; se não achar, usa a sua de teste local
SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-%mopyw^rlc0ul+cxut*y7^d@u%(zai+ny8r%-8ao8h7+xju0yd"
)

# Se a variável DEBUG não estiver definida no ambiente, assume True (local)
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Garanta que o link do Railway está nos hosts permitidos
ALLOWED_HOSTS = [
    "wctoilet-production.up.railway.app",
    "127.0.0.1",
    "localhost",
    "*.up.railway.app",  # Coringa para aceitar subdomínios do Railway
]

# Configuração crucial para proxies como o Railway entenderem o HTTPS de ponta a ponta
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Variações explícitas exigidas pelo mecanismo de CSRF do Django em produção
CSRF_TRUSTED_ORIGINS = [
    "https://wctoilet-production.up.railway.app",
    "https://*.up.railway.app",
    "http://127.0.0.1",
    "http://localhost",
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "controle_banheiro",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Essencial para os arquivos estáticos na nuvem!
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "setup.urls"

# setup/settings.py

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # AJUSTE AQUI: Diz ao Django para buscar na pasta global 'templates'
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "setup.wsgi.application"


# Database Config - Inteligente para Local e Produção
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "toilet_db",
        "USER": "professor",
        "PASSWORD": "Luc1An475",
        "HOST": "localhost",
        "PORT": "5434",
    }
}

# Se o Railway injetar a DATABASE_URL, ele sobrescreve a configuração local automaticamente
if os.environ.get("DATABASE_URL"):
    DATABASES["default"] = dj_database_url.config(conn_max_age=600, ssl_require=True)


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization (Configurado para o padrão brasileiro de fuso/idioma)
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Armazenamento otimizado para produção usando WhiteNoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# setup/settings.py

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "login"


# Se estiver no Railway (Produção), força os cookies a trafegarem apenas via HTTPS
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
