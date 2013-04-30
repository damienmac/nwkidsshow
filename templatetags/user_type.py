from django import template
from django.template import resolve_variable, NodeList
from views import user_is_exhibitor, user_is_retailer

register = template.Library()

# factored out common code into this helper function
def ifattendee(parser, endstring, checknode_class):
    nodelist_true = parser.parse(('else', endstring))
    token = parser.next_token()

    if token.contents == 'else':
        nodelist_false = parser.parse((endstring,))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()

    return checknode_class(nodelist_true, nodelist_false)

@register.tag(name='ifexhibitor')
def ifexhibitor(parser, token):
    """ Check to see if the currently logged in user is an exhibitor.
    Use the helper methods in views.py instead of re-implementing here

    Usage: {% ifexhibitor %} ... {% endifexhibitor %}, or
           {% ifexhibitor %} ... {% else %} ... {% endifexhibitor %}

    """
    return ifattendee(parser, 'endifexhibitor', ExhibitorCheckNode)

@register.tag(name='ifretailer')
def ifretailer(parser, token):
    """ Check to see if the currently logged in user is a retailer.
    Use the helper methods in views.py instead of re-implementing here

    Usage: {% ifretailer %} ... {% endifretailer %}, or
           {% ifretailer %} ... {% else %} ... {% endifretailer %}

    """
    return ifattendee(parser, 'endifretailer', RetailerCheckNode)

# factored out common code into this base class
class AttendeeCheckNode(template.Node):

    def __init__(self, nodelist_true, nodelist_false, check_helper):
        self.nodelist_true  = nodelist_true
        self.nodelist_false = nodelist_false
        self.check_helper   = check_helper

    def render(self, context):
        user = resolve_variable('user', context)

        if not user.is_authenticated():
            return self.nodelist_false.render(context)

        if self.check_helper(user):
            return self.nodelist_true.render(context)

        return self.nodelist_false.render(context)


class ExhibitorCheckNode(AttendeeCheckNode):
    def __init__(self, nodelist_true, nodelist_false):
        super(ExhibitorCheckNode, self).__init__(nodelist_true, nodelist_false, user_is_exhibitor)

class RetailerCheckNode(AttendeeCheckNode):
    def __init__(self, nodelist_true, nodelist_false):
        super(RetailerCheckNode, self).__init__(nodelist_true, nodelist_false, user_is_retailer)
