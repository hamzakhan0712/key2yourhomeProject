from django import template
from django.contrib.humanize.templatetags.humanize import intcomma

register = template.Library()

@register.filter(name='indian_currency')
def format_indian_currency(value):
    """
    Format value in Indian currency notation with appropriate suffix
    """
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
        
    if value < 1000:
        return f"{intcomma(int(value))}"
    elif 1000 <= value < 100000:
        thousands = value / 1000
        if thousands.is_integer():
            return f"{int(thousands)} thousand"
        return f"{thousands:.1f} thousand"
    elif 100000 <= value < 10000000:
        lakhs = value / 100000
        if lakhs.is_integer():
            return f"{int(lakhs)} lakh"
        return f"{lakhs:.1f} lakh"
    else:
        crores = value / 10000000
        if crores.is_integer():
            return f"{int(crores)} crore"
        return f"{crores:.1f} crore"