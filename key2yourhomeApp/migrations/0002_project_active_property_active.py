# Generated by Django 5.2.1 on 2025-05-30 05:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('key2yourhomeApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='property',
            name='active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]
