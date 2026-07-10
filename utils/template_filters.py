"""
Jinja2 template filters for LearnMate AI.
Register in app.py via app.jinja_env.filters.
"""
import json as _json


def from_json(value):
    """Parse a JSON string in templates."""
    try:
        return _json.loads(value)
    except Exception:
        return value
