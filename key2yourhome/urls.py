"""
URL configuration for key2yourhome project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path   # 👉 A. include already imported
from django.conf import settings         # 👉 B. Import settings
from django.conf.urls.static import static  # 👉 C. Import static helper
from django.views.static import serve as media_serve
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from key2yourhomeApp.sitemaps import StaticViewSitemap, ProjectSitemap, PropertySitemap


sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'properties': PropertySitemap,
}


urlpatterns = [
    path('grappelli/', include('grappelli.urls')), # grappelli URLS
    path('admin/', admin.site.urls),
    path('', include('key2yourhomeApp.appurls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
        # Robots.txt
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    )),
]


# 👉 F. Serve static and media files during development only
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', media_serve, {
            'document_root': settings.STATIC_ROOT,
        }),
        re_path(r'^media/(?P<path>.*)$', media_serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
        
    ]

