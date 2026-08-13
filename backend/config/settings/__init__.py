from .base import *

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'testing':
    from .testing import *
else:
    from .development import *
