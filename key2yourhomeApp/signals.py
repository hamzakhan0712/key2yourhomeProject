# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.postgres.search import SearchVector
from models import Project, Property

@receiver(post_save, sender=Project)
def update_project_search_vector(sender, instance, **kwargs):
    # Ensure we're only updating when needed
    if kwargs.get('created', False) or kwargs.get('update_fields', None) is None:
        sender.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('name', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('city', weight='C') +
            SearchVector('locality', weight='C') +
            SearchVector('address', weight='D')
        )

@receiver(post_save, sender=Property)
def update_property_search_vector(sender, instance, **kwargs):
    if kwargs.get('created', False) or kwargs.get('update_fields', None) is None:
        sender.objects.filter(pk=instance.pk).update(
            search_vector=SearchVector('property_code', weight='A') +
            SearchVector('description', weight='B') +
            SearchVector('city', weight='C') +
            SearchVector('address', weight='C') +
            SearchVector('society_name', weight='D')
        )