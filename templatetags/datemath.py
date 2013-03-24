from lib2to3.patcomp import _type_of_literal
from django import template
import datetime
register = template.Library()

@register.filter(name='dayadd')
def dayadd(date, numdays):
    """
    given a datetime.date object and a number of days to add to that date,
    return a new datetime.date object as date + numdays
    """
    return date + datetime.timedelta(days=numdays)
