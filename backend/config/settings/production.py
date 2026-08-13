import os

DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'waterweb.example.com').split(',')

SECURE_SSL_REDIRECT = os.environ.get('FORCE_HTTPS', 'False').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'https://waterweb.example.com').split(',')
