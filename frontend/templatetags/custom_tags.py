# your_app/templatetags/custom_tags.py

from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Safely get d[key] or empty list."""
    return d.get(key, [])
