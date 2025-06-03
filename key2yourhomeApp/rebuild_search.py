# management/commands/rebuild_search_vectors.py
from django.core.management.base import BaseCommand
from django.contrib.postgres.search import SearchVector

from models import Project, Property

class Command(BaseCommand):
    help = 'Rebuild search vectors for all models'

    def handle(self, *args, **options):
        self.stdout.write("Rebuilding project search vectors...")
        Project.objects.update(
            search_vector=(
                SearchVector('name', weight='A') +
                SearchVector('description', weight='B') +
                SearchVector('city', weight='B') +
                SearchVector('locality', weight='B') +
                SearchVector('district', weight='C') +
                SearchVector('state', weight='C') +
                SearchVector('address', weight='C') +
                SearchVector('landmark', weight='D') +
                SearchVector('developed_by', weight='D')
            )
        )
        
        self.stdout.write("Rebuilding property search vectors...")
        Property.objects.update(
            search_vector=(
                SearchVector('property_code', weight='A') +
                SearchVector('description', weight='B') +
                SearchVector('city', weight='B') +
                SearchVector('locality', weight='B') +
                SearchVector('district', weight='C') +
                SearchVector('state', weight='C') +
                SearchVector('address', weight='C') +
                SearchVector('society_name', weight='C') +
                SearchVector('landmark', weight='D')
            )
        )
        
        self.stdout.write(self.style.SUCCESS("Successfully rebuilt all search vectors"))






