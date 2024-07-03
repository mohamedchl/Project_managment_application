print("update_disponibilite.py loaded")

from django.core.management.base import BaseCommand
from django.utils import timezone
from Gestion_projet.models import Projet

class Command(BaseCommand):
    help = 'Updates disponibilite of associated resources when date_fin is reached'

    def handle(self, *args, **options):  # This method must be named handle
        today = timezone.now().date()
        for projet in Projet.objects.all():
            if projet.date_fin <= today:
                projet.etat = "finis"
                projet.save()
                self.stdout.write(f'Projet "{projet.nom_projet}" (ID: {projet.id_projet}) est "finis".')
        self.stdout.write('Mise a jour de l etat projet est fait.')
