# search/utils.py
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from models import *

class SearchEngine:
    @staticmethod
    def search_properties(query, filters=None):
        """
        Search properties with full-text search and filters
        """
        if filters is None:
            filters = {}
        
        # Base queryset
        properties = Property.objects.all()
        
        # Full-text search
        if query:
            search_query = SearchQuery(query, config='english')
            properties = properties.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-rank')
        
        # Apply filters
        if filters.get('property_type'):
            properties = properties.filter(property_type=filters['property_type'])
        
        if filters.get('city'):
            properties = properties.filter(city__iexact=filters['city'])
        
        # Add more filters as needed...
        
        return properties.distinct()

    @staticmethod
    def search_projects(query, filters=None):
        """
        Search projects with full-text search and filters
        """
        if filters is None:
            filters = {}
        
        # Base queryset
        projects = Project.objects.all()
        
        # Full-text search
        if query:
            search_query = SearchQuery(query, config='english')
            projects = projects.annotate(
                rank=SearchRank('search_vector', search_query)
            ).filter(search_vector=search_query).order_by('-search_rank')
        
        # Apply filters
        if filters.get('project_type'):
            projects = projects.filter(project_type=filters['project_type'])
        
        if filters.get('city'):
            projects = projects.filter(city__iexact=filters['city'])
        
        # Add more filters as needed...
        
        return projects.distinct()

    @staticmethod
    def get_suggestions(query, search_type=None, limit=5):
        """
        Get search suggestions based on query
        """
        suggestions = SearchSuggestion.objects.filter(
            term__istartswith=query
        )
        
        if search_type:
            suggestions = suggestions.filter(search_type=search_type)
            
        return suggestions.order_by('-weight', '-use_count')[:limit]