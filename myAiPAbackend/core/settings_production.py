# core/settings_production.py
# Production settings for myAiPA deployed on Railway.
# Extends base settings.py with production-specific config.
# Never run this locally — only on Railway.

from .settings import *
import dj_database_url

# Security
DEBUG = False
ALLOWED_HOSTS = [
    '.railway.app',
    '.up.railway.app',
]

# Database — Railway provides DATABASE_URL env variable
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        ssl_require=True,
    )
}

# Static files — whitenoise serves them directly
STATICFILES_STORAGE = (
    'whitenoise.storage.CompressedManifestStaticFilesStorage'
)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise middleware — must be second after Security
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# CORS — will add Vercel URL after frontend deployment
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]