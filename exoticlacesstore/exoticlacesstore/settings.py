"""
Django settings for exoticlacesstore project.
"""

from pathlib import Path
import os
from decouple import config  # Add this import




# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# SECURITY & CORE SETTINGS
# ============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
#SECRET_KEY = config('DJANGO_SECRET_KEY')
SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-i%*cv7fd_24c0!i2usif7#l=wn@vsfv-h@32voan7m3dqy_$qu')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')





# ============================================================================
# APPLICATION DEFINITION
# ============================================================================

INSTALLED_APPS = [
    'lacesstore',
    'payments',
    'shipping',
    'currency',
    'kwantacious',
    'vendor_products',
    'crispy_forms',
    'crispy_bootstrap4',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_facebook_capi',
    'django_recaptcha',
    #'web3_payment',
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
    'allauth.account.middleware.AccountMiddleware',
    'lacesstore.middleware.VisitorTrackingMiddleware',
    
]

ROOT_URLCONF = 'exoticlacesstore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'lacesstore.context_processors.menu_links',
                'lacesstore.context_processors.counter',
                'lacesstore.context_processors.orderid',
                'currency.context_processors.currency_context',
                'lacesstore.context_processors.social_links',
                'lacesstore.context_processors.facebook_pixel',
                'lacesstore.context_processors.sale_context',  # Add this
                'vendor_products.views.vendor_products_home_context',  # Add this
                'vendor_products.context_processors.vendor_cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'exoticlacesstore.wsgi.application'

# settings.py

# Add this line - CSRF Trusted Origins for production
CSRF_TRUSTED_ORIGINS = [
    'https://plankton-app-caule.ondigitalocean.app',
    'https://www.plankton-app-caule.ondigitalocean.app',
    'https://exoticlaces.com',
    'https://www.exoticlaces.com',
    
]



# settings.py
import os
from decouple import config

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='defaultdb'),
        'USER': config('DB_USER', default='doadmin'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='25060'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            # 'ssl': {
            #     'ca': os.path.join(BASE_DIR, 'ca-certificate.crt')
            # },
        },
    }
}

# ============================================================================
# PASSWORD VALIDATION
# ============================================================================

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

# ============================================================================
# INTERNATIONALIZATION
# ============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ============================================================================
# AUTHENTICATION (Django Allauth)
# ============================================================================

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = config('SITE_ID', default=2, cast=int)

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
# ACCOUNT_EMAIL_REQUIRED = True
# ACCOUNT_AUTHENTICATION_METHOD = 'email'
# ACCOUNT_USERNAME_REQUIRED = True
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_LOGIN_URL = '/account/signin/'
LOGIN_URL = '/account/signin/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/account/create/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/'
PASSWORD_RESET_TIMEOUT = 14400

# ============================================================================
# EMAIL (Resend SMTP)
# ============================================================================

#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'lacesstore.email_backend.RetryEmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = config('RESEND_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@mail.exoticlaces.com')
EMAIL_TIMEOUT = 30

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Fixed: STATICFILES_DIRS

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'static', 'media')

# ============================================================================
# PAYSTACK
# ============================================================================
PAYSTACK_PUBLIC_KEY = config('PAYSTACK_PUBLIC_KEY', default='')
PAYSTACK_SECRET_KEY = config('PAYSTACK_SECRET_KEY', default='')
PAYSTACK_BASE_URL = "https://api.paystack.co"
PAYSTACK_SUPPORTED_CURRENCIES = ["NGN", "GHS", "USD", "XOF"]

# ============================================================================
# CRISPY FORMS
# ============================================================================

CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

# ============================================================================
# CURRENCY
# ============================================================================

DEFAULT_CURRENCY = config('DEFAULT_CURRENCY', default='NGN')
SUPPORTED_CURRENCIES = ["NGN", "GHS", "XOF", "USD", "EUR"]
EXCHANGE_RATE_API_KEY = config('EXCHANGE_RATE_API_KEY', default='')

# ============================================================================
# ANALYTICS
# ============================================================================

GOOGLE_ANALYTICS_ID = config('GOOGLE_ANALYTICS_ID', default='')
GOOGLE_ANALYTICS_DEBUG = False  # Set to True in development

# ============================================================================
# FACEBOOK PIXEL
# ============================================================================

FACEBOOK_PIXEL_ID = config('FACEBOOK_PIXEL_ID', default='')
FACEBOOK_CAPI_ACCESS_TOKEN = config('FACEBOOK_CAPI_ACCESS_TOKEN', default='')

# ============================================================================
# DEFAULT PRIMARY KEY
# ============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py

# Security Headers
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
X_FRAME_OPTIONS = "SAMEORIGIN"  # Change from ALLOWALL for production
# SECURE_SSL_REDIRECT = True  # If you have SSL (you will on DigitalOcean)
# SECURE_HSTS_SECONDS = 31536000  # 1 year (enable after SSL is working)
# CSRF_COOKIE_SECURE = True  # Send CSRF cookie only over HTTPS
# SESSION_COOKIE_SECURE = True  # Send session cookie only over HTTPS


CSRF_COOKIE_SECURE = True  # ✅ Safe - only send over HTTPS
SESSION_COOKIE_SECURE = True  # ✅ Safe - only send over HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Additional Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True


# settings.py

# DigitalOcean Spaces Configuration
# settings.py

# DigitalOcean Spaces Configuration
# Use Spaces if AWS credentials are available, regardless of DEBUG
# settings.py

# DigitalOcean Spaces Configuration
if config('AWS_ACCESS_KEY_ID', default='') and config('AWS_SECRET_ACCESS_KEY', default=''):
    # Install storages if not already installed
    # INSTALLED_APPS += ['storages']  # Already done
    
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = 'exoticlaces-media'
    AWS_S3_REGION_NAME = 'fra1'
    AWS_S3_ENDPOINT_URL = 'https://fra1.digitaloceanspaces.com'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.fra1.digitaloceanspaces.com'
    
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    
    # ✅ Override MEDIA_URL to use Spaces
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
    
    # ⚠️ MEDIA_ROOT is not used with Spaces, but keep it as fallback
    MEDIA_ROOT = os.path.join(BASE_DIR, 'static', 'media')
    
    # ✅ Optional: Add a log to confirm Spaces is being used
    print("✅ Using DigitalOcean Spaces for media files")
else:
    # Fallback to local storage
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'static', 'media')
    print("⚠️ Using local media storage")



# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}


CSRF_FAILURE_VIEW = 'lacesstore.views.csrf_failure'



RECAPTCHA_PUBLIC_KEY = config('RECAPTCHA_PUBLIC_KEY', default='')
RECAPTCHA_PRIVATE_KEY = config('RECAPTCHA_PRIVATE_KEY', default='')




# Web3 Payment Settings
WEB3_PAYMENT = {
    'DEFAULT_NETWORK': 'polygon',
    'DEFAULT_TOKEN': 'USDC',
    'PAYMENT_EXPIRY_MINUTES': 60,
    'CONFIRMATIONS_REQUIRED': 12,
    'ENABLE_TESTNET': False,
}

# Celery for background tasks
CELERY_BEAT_SCHEDULE = {
    'monitor-web3-payments': {
        'task': 'web3_payment.tasks.monitor_payments',
        'schedule': 60.0,  # Every minute
    },
}



# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}