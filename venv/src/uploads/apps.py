from django.apps import AppConfig

from .models import Document
class UploadsConfig(AppConfig):
    name = 'uploads'
admin.site.register(Document)