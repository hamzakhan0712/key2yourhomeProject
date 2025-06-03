from django import template
from ..models import Bookmark

register = template.Library()

@register.simple_tag(takes_context=True)
def is_property_bookmarked(context, property):
    request = context['request']
    if not request.user.is_authenticated:
        return False
    return Bookmark.objects.filter(user=request.user, property=property).exists()

@register.simple_tag(takes_context=True)
def is_project_bookmarked(context, project):
    request = context['request']
    if not request.user.is_authenticated:
        return False
    return Bookmark.objects.filter(user=request.user, project=project).exists()