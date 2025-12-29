import sys

from api import routes as _routes

sys.modules[__name__] = _routes
