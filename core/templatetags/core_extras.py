from django import template
import core.utils

register = template.Library()


@register.filter
def get_key_dict(d, key):
    return d[key]


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr)


@register.filter
def float_formatter(x, num_digits=3):
    try:
        float(x)
    except ValueError:
        return ''
    return core.utils.float_formatter(x, num_digits=num_digits)


@register.filter
def percentage(x, num_digits=None):
    return float_formatter(100 * x, num_digits=num_digits)


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
def absolute(value):
    return abs(value)
