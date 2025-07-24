import os
env = os.environ.get('DJANGO_ENV') or 'development'
if env == 'production':
    from .production import *
elif env == 'testing':
    from .testing import *
else:
    from .development import *
