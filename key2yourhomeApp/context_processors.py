from .models import Project, Property

def project_property_context(request):
    return {
        'navbar_projects': Project.objects.all(),
        'navbar_properties': Property.objects.all(),
    }


# In your_app/context_processors.py

from django.contrib.humanize.templatetags.humanize import intcomma

def indian_currency_format(request):
    def format_currency(value):
        value = float(value)
        if value < 1000:
            return f"₹{intcomma(int(value))}"
        elif 1000 <= value < 100000:
            thousands = value / 1000
            return f"₹{intcomma(int(value))} ({thousands:.1f} thousand)" if thousands != int(thousands) else f"₹{intcomma(int(value))} ({int(thousands)} thousand)"
        elif 100000 <= value < 10000000:
            lakhs = value / 100000
            return f"₹{intcomma(int(value))} ({lakhs:.1f} lakh)" if lakhs != int(lakhs) else f"₹{intcomma(int(value))} ({int(lakhs)} lakh)"
        else:
            crores = value / 10000000
            return f"₹{intcomma(int(value))} ({crores:.1f} crore)" if crores != int(crores) else f"₹{intcomma(int(value))} ({int(crores)} crore)"
    
    return {'indian_currency': format_currency}