from django.contrib import sitemaps
from django.urls import reverse
from .models import Project, Property

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return [
            'landing_page',
            'about',
            'contact_us',
            'privacy_policy',
            'terms_conditions',
            'faqs',
            'project_list',
            'property_list',
        ]

    def location(self, item):
        return reverse(item)

class ProjectSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Project.objects.filter(active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('project_detail', kwargs={'pk': obj.pk})

class PropertySitemap(sitemaps.Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Property.objects.filter(active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return reverse('property_list')