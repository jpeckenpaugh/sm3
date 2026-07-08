
from pathlib import Path

from db import list_databases, get_active_db_name

class _SafeCache(dict):
    def get(self, key, default=None):
        try:
            k = _safe_key(key)
            return dict.get(self, k, default)
        except (KeyError, TypeError):
            return default
    def __setitem__(self, key, value):
        dict.__setitem__(self, _safe_key(key), value)
    def __contains__(self, key):
        try:
            return _safe_key(key) in dict.keys(self)
        except TypeError:
            return False

def _safe_key(key):
    if isinstance(key, tuple):
        return tuple(
            tuple(sorted(d.items())) if isinstance(d, dict) else d
            for d in key
        )
    return key

import jinja2
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(Path(__file__).parent / 'templates')),
    autoescape=jinja2.select_autoescape(['html', 'xml']),
)
env.cache = _SafeCache()

from starlette.templating import _TemplateResponse
from starlette.requests import Request

def tr(self, *args):
    if len(args) == 3 and isinstance(args[0], Request):
        request, name, ctx = args
        ctx['request'] = request
    elif len(args) == 2:
        name, ctx = args
    else:
        name, ctx = args[0], {}
    # Inject database context into every template
    ctx.setdefault('databases', list_databases())
    ctx.setdefault('active_db_name', get_active_db_name())
    return _TemplateResponse(env.get_template(name), ctx)

templates = type('T', (), {'env': env, 'TemplateResponse': tr})()
