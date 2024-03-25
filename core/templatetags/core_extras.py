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
    return core.utils.float_formatter(x, num_digits=num_digits)
