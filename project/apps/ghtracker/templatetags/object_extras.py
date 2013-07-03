from django import template

register = template.Library()

def key(obj,key):
    changes = obj.get(key,{}).get('changes',0)
    return changes

register.filter('key', key)
