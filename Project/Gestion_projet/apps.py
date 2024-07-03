from django.apps import AppConfig

class GestionProjetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Gestion_projet'

    def ready(self):
        import Gestion_projet.signals  # Import signals.py here
