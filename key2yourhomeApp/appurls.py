from django.urls import path
from .views import *
from .sitemaps import StaticViewSitemap, ProjectSitemap, PropertySitemap
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap



sitemaps = {
    'static': StaticViewSitemap,
    'projects': ProjectSitemap,
    'properties': PropertySitemap,
}



urlpatterns = [



    # Authentication
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Password management
    path('forgot-password/', forgot_password_view, name='forgot_password'),
    path('reset-password/<str:token>/', reset_password_view, name='reset_password'),
    path('change-password/', change_password_view, name='change_password'),
    
    # Profile management
    path('profile/', profile_view, name='profile'),
    path('profile/sessions/<int:session_id>/terminate/', terminate_session_view, name='terminate_session'),
    path('profile/delete/', delete_profile_view, name='delete_profile'),

    path('', landing_page, name='landing_page'),  # Root URL for landing page
    path('search/', unified_search, name='unified_search'),
    path('search/suggest/', search_suggestions, name='search_suggestions'),

    path('project_list/', project_list, name='project_list'),
    path('projects/<int:pk>/', project_detail, name='project_detail'),
    path('project/<int:pk>/review/', submit_project_review, name='submit_project_review'),
     
    path('bookmarks/', my_bookmarks, name='my_bookmarks'),
    path('bookmarks/project/<int:project_id>/bookmark/', add_project_bookmark, name='add_project_bookmark'),
    path('bookmarks/property/<int:property_id>/bookmark/', add_property_bookmark, name='add_property_bookmark'),
    path('bookmarks/remove/<int:bookmark_id>/', remove_bookmark, name='remove_bookmark'),


    path('property_list/', property_list, name='property_list'),


    path('about/', about, name='about'),  
    path('contact_us/', contact_us, name='contact_us'),
    path('privacy_policy/', privacy_policy, name='privacy_policy'),
    path('terms_conditions/', terms_conditions, name='terms_conditions'),  
    path('faqs/', faqs, name='faqs'),   

]