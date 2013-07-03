from settings import *
import dj_database_url
import sys

DEBUG = os.environ.get('DEBUG', False)

DATABASES = {
    'default': dj_database_url.config(default='postgres://localhost'),
}

SERVE_STATIC = os.environ.get('SERVE_STATIC', True)
