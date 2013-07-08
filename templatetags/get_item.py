from django import template
register = template.Library()

## This kindof sucks.
## It defeats one of the tenants of separation of data in Django.
## So be careful.

@register.filter(name='get_item')
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None
