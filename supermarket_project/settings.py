from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-supermarket-secret-key-change-in-production'
DEBUG = True  # change back to True for local development

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'keniwaithera-cmyk.pythonanywhere.com']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'supermarket',
    'django_daraja',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Locks the entire portal behind login. Individual views can opt out with
    # the @login_not_required decorator (used only for the M-Pesa webhook and
    # the PWA service worker, which must stay publicly reachable).
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'supermarket_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'supermarket' / 'templates'],
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

WSGI_APPLICATION = 'supermarket_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'supermarket' / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# M-Pesa Daraja API credentials
MPESA_ENVIRONMENT = 'sandbox'  # change to 'production' when going live

MPESA_CONSUMER_KEY = 't3qkaGqEaUABpgsJr9eenFFOkqpAAWoRmlkQ1b2Wgc17ibij'
MPESA_CONSUMER_SECRET = 'Q32siYmwgAoxZTosXbYTRgqS2usntUNKORKufvUkNwxbLrB15Kk8Yvvrmk6w07zh'
MPESA_EXPRESS_SHORTCODE = '174379'
MPESA_SHORTCODE_TYPE = 'paybill'  # or ''
MPESA_PASSKEY = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

MPESA_CALLBACK_URL = 'https://your-ngrok-url.ngrok.io/mpesa/callback/ '

# ─────────────────────────────────────────
# AUTHENTICATION / SINGLE-ADMIN PORTAL
# ─────────────────────────────────────────
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
# Signed-out sessions default to expiring when the browser closes unless the
# user ticks "Remember me" on the login page (handled in BrandedLoginView).
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days when "remember me" is checked

# Optional WhatsApp (Twilio) notification settings
# To enable, set WHATSAPP_NOTIFICATIONS_ENABLED = True and provide Twilio credentials.
WHATSAPP_NOTIFICATIONS_ENABLED = False
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_WHATSAPP_FROM = ''  # e.g. 'whatsapp:+1415XXXXXXX'
# Manager number to receive new-chat alerts (use international format, e.g. +2547...)
MANAGER_WHATSAPP_NUMBER = ''
# If True, also send an acknowledgement message to the customer (requires customer's phone)
NOTIFY_CUSTOMER_ON_SUBMIT = False
