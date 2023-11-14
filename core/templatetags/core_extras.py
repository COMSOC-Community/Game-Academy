from django import template

register = template.Library()


# @register.filter
# def addstr(x, y):
#     return str(x) + str(y)


@register.filter
def get_key_dict(d, key):
    return d[key]


@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr)
