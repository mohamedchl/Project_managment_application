from typing import Iterable
from django.db import models,transaction
from datetime import datetime
from calendar import monthrange
from django.contrib.auth.models import User, Group
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.db.models import Q,F
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _
from django import forms



class CaseInsensitiveModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        case_sensitive_username = {'username__exact': username}
        try:
            user = UserModel._default_manager.get(**case_sensitive_username)
        except UserModel.DoesNotExist:
            return None

        if user.check_password(password):
            return user
        
class Marchet(models.Model):
    id_marchet = models.AutoField(primary_key=True)
    lib_marchet = models.CharField(max_length = 30)
    details = models.TextField()
    def __str__(self):
        return (self.lib_marchet)
    
class MaitreOuvrage(models.Model):
    id_mouvrage = models.AutoField(primary_key=True)
    lib_mouvrage = models.CharField(max_length = 30)
    details = models.TextField()
    def __str__(self):
        return (self.lib_mouvrage)
    
from django.db import models
from django.utils.timezone import now

class EtatProjet(models.Model):
    id_etat = models.AutoField(primary_key=True)
    lib_etat = models.CharField(max_length=30)
    date_etat = models.DateField(default=now)
    projet = models.ForeignKey("Projet", related_name="etat", on_delete=models.CASCADE)

    def __str__(self):
        return self.lib_etat


    
class Notification(models.Model):
    Type_notif = (
        ('1','Information'),
        ('2','Avertissement'),
        ('3','Problème'),
    )
    id_notification =  models.AutoField(primary_key=True)
    type =  models.CharField(max_length=1 , choices = Type_notif)
    titre = models.CharField(max_length = 100)
    date = models.DateTimeField(default=datetime.now)
    details = models.TextField()
    employe = models.ManyToManyField("Employe", blank=True, related_name="notifications")
    def __str__(self):
        return (self.titre)
    
        

class Employe(models.Model):
    Poste_agent = (
        ('1', 'President Directeur Générale'),
        ('2', 'Directeur Générale'),
        ('3', 'Assistant'),
        ('4', 'Consultant')                                        
        ,('5', 'Chef Stucture')
        ,('6', 'Ingénieur d informatique') 
        ,('7', 'Ingénieur D Etudes')
        ,('8','Chargé D Etudes ')
        ,('9','Exploitant ')
        ,('10','Ingénieur de Génie Civile')
        ,('11','Chef Projet') 
        ,('12','Chef Tache')
        ,('13','Autre')
    )
    Etat_employee=(
        ('1','Célibataire'),
        ('2','Mariée'),
    )
    id_employe = models.AutoField(primary_key=True)
    nom_employe = models.CharField(max_length=50)
    email_employe = models.CharField(max_length=50, unique=True)
    telephone = models.BigIntegerField(null=True, blank=True)
    bureau = models.CharField(max_length=20)
    matricule = models.BigIntegerField(unique=True)
    etat_employe = models.CharField(max_length=30, choices=Etat_employee,default='1')
    poste = models.CharField(max_length=3, choices=Poste_agent)
    notificationNotSeen = models.IntegerField(blank=True, default=0)  
    incidentNotSeen = models.IntegerField(blank=True, default=0)  
    def __str__(self):
        return self.nom_employe
    
    
class NotificationSeen(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    seen = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.notification.titre}"
    
class Incident(models.Model):
    id_incident = models.AutoField(primary_key=True)
    nom_incident = models.CharField(max_length=60)
    date_incident = models.DateField(default=datetime.now)
    details = models.TextField()
    pourcentage = models.FloatField()
    progress = models.FloatField()
    agentDeclencheur = models.ForeignKey(Employe, on_delete=models.SET_NULL,blank=True,null=True)
    projet = models.ForeignKey("Projet", on_delete=models.CASCADE)
    employe = models.ManyToManyField("Employe", blank=True, related_name="incidents")
    tache = models.ForeignKey("Tache",blank=False, related_name="incidents", on_delete=models.CASCADE,default=None,null=False)
    def __str__(self):
        return (self.nom_incident)
    
    
    @property
    def update_progress(self):
        sibling_incidents = Incident.objects.filter(tache=self.tache)
        sibling_taches = Tache.objects.filter(tache_mere=self.tache.tache_mere, projet=self.projet)
        
        total_sibling_progress = sum(incident.progress * (incident.pourcentage / 100) for incident in sibling_incidents)
        total_sibling_progress += sum(tache.progress * (tache.pourcentage / 100) for tache in sibling_taches)
        
        
        if self.tache.progress != total_sibling_progress:
            self.tache.progress = total_sibling_progress
            self.tache.save()  # Save the updated progress of the associated tache
                        
        self.progress = float("{:.3f}".format(self.progress))
        
            

    
class IncidentSeen(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    seen = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.user.username} - {self.incident.nom_incident}"

class SuiviIncident(models.Model):
    id_suivi = models.AutoField(primary_key=True)
    date_suivi = models.DateField(default=datetime.now)
    details = models.TextField()
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    employe = models.ForeignKey(Employe,on_delete=models.CASCADE,related_name="suiviIncident",null=True)

    def __str__(self):
        return (f"le suivi d'incident "+self.incident.nom_incident)

from django.db import models, transaction
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

class Projet(models.Model):
    avancement_choices = [
        ('1', 'normal'),
        ('2', 'bien'),
        ('3', 'trés bien'),
        ('4', 'mauvaise'),
        ('5', 'trés mauvaise'),
        ('6', 'pas encore commencé'),
        ('7', 'Terminé'),
    ]
    id_projet = models.AutoField(primary_key=True)
    nom_projet = models.CharField(max_length=50, unique=True)
    date_debut = models.DateField(default=now)
    date_fin = models.DateField(default=now)
    details = models.TextField()
    maitreOuvrage = models.ForeignKey('MaitreOuvrage', on_delete=models.SET_NULL, null=True)
    progress = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)], null=True, blank=True)
    chefProjet = models.ForeignKey('Employe', on_delete=models.CASCADE, related_name="projet_chef")
    marchet = models.ForeignKey('Marchet', on_delete=models.SET_NULL, null=True, blank=True, related_name="projet")
    employe = models.ManyToManyField("Employe", blank=True, related_name="projets")
    latest_etat = models.CharField(max_length=30, blank=True, null=True)
    avancement = models.CharField(max_length=30, default='1', choices=avancement_choices)

    def __str__(self):
        return self.nom_projet

    def save(self, *args, **kwargs):
        if self.chefProjet:
            self.chefProjet.poste = '11'
            self.chefProjet.save()

        self.date_debut = datetime.combine(self.date_debut, datetime.min.time())
        self.date_fin = datetime.combine(self.date_fin, datetime.min.time())

        duree = (self.date_fin - self.date_debut).days
        dureeD = (datetime.now() - self.date_debut).days
        if dureeD == 0:
            dureeD = 1

        create_etat = False
        if self.progress == 100 or datetime.now() > self.date_fin:
            self.avancement = '7'
            if not EtatProjet.objects.filter(projet=self, lib_etat='finis').exists():
                create_etat = True
        else:
            progressParJour = self.progress / dureeD
            if progressParJour == 0:
                self.avancement = '6'
            elif progressParJour * duree == 100:
                self.avancement = '1'
            elif 50 <= progressParJour * duree < 100:
                self.avancement = '4'
            elif progressParJour * duree < 50:
                self.avancement = '5'
            elif 100 < progressParJour * duree < 150:
                self.avancement = '2'
            elif progressParJour * duree >= 150:
                self.avancement = '3'

        self.progress = float("{:.3f}".format(self.progress))
        super().save(*args, **kwargs)

        print(self.avancement)
        if create_etat:
            EtatProjet.objects.create(lib_etat='finis', date_etat=datetime.now(), projet=self)
       


    
class Tache(models.Model):
    TYPE_CHOICES = [
        ('1', 'Tâche simple'),
        ('2', 'Tâche besoin d un suivi'),
    ]
    avancement_choices = [
        ('1', 'normal'),
        ('2', 'bien'),
        ('3', 'trés bien'),
        ('4', 'mauvaise'),
        ('5', 'trés mauvaise'),
        ('6', 'pas encore commencé'),
        ('7', 'Terminé'),
    ]
    id_tache = models.AutoField(primary_key=True)
    nom_tache = models.CharField(max_length=60)
    date_debut = models.DateField(default=datetime.now)
    date_fin = models.DateField(default=datetime.now)
    details = models.TextField(null=True,blank=True)
    pourcentage = models.FloatField(default=0)
    progress = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)],null = True,blank = True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default = '2')
    tache_mere = models.ForeignKey("self", on_delete=models.CASCADE, related_name="sous_taches", null=True, blank=True)
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE,related_name="taches")
    employe = models.ManyToManyField("Employe", blank=True, related_name="taches")
    chef_tache = models.ForeignKey("Employe", blank=True,null=True, related_name="chef_taches",on_delete=models.SET_NULL,)
    #avancement ytaficha ghir f dashboard t3 tache sma ytinitializa tmak brk
    avancement = models.CharField(max_length=30,default='1', choices=avancement_choices)

    def __str__(self):
        return (self.nom_tache+"- projet: "+self.projet.nom_projet)
    
    def save(self, *args, **kwargs):


        chef_tache = self.chef_tache
        # Handle chef_tache when the instance is created
        if not self.pk:
            if chef_tache:
                chef_tache.poste = '12'
                chef_tache.save()
        else:
            if chef_tache:
                chef_tache.poste = '12'
                chef_tache.save()
            if self.sous_taches.exists():
                self.sous_taches.first().save()
    
        self.date_debut = datetime.combine(self.date_debut, datetime.min.time())
        self.date_fin = datetime.combine(self.date_fin, datetime.min.time())
        duree=(self.date_fin-self.date_debut).days
        dureeD = (datetime.now() - self.date_debut).days
        if dureeD == 0:
            dureeD=1
        if self.progress == 100 or datetime.now()>self.date_fin:
            self.avancement='7'
            print(self.avancement)
        else:
            progressParJour = self.progress/dureeD
            if progressParJour == 0:
                self.avancement='6'   
            elif progressParJour*duree == 100:
                self.avancement='1'
            elif progressParJour*duree<100 and progressParJour*duree>=50:
                self.avancement='4'
            elif progressParJour*duree<50:
                self.avancement='5'
            elif progressParJour*duree>100 and progressParJour*duree<150:
                self.avancement='2'
            elif progressParJour*duree>=150:
                self.avancement='3'
        self.progress = float("{:.3f}".format(self.progress))
        
        super().save(*args, **kwargs)
        
        
    
    @property
    def update_progress(self):
        if self.sous_taches.exists():  # Check if there are any subtasks
            return
        # Calculate progress for current tache
        total_progress = self.progress * (self.pourcentage / 100)
        
        # Update progress of parent taches recursively
        parent_tache = self.tache_mere
        while parent_tache is not None:
            sibling_taches = Tache.objects.filter(tache_mere=parent_tache, projet=self.projet)
            parent_progress = sum(tache.progress * (tache.pourcentage / 100) for tache in sibling_taches)
            sibling_incidents = Incident.objects.filter(tache=parent_tache)
            print(sibling_incidents)
            if sibling_incidents:
                parent_progress+=sum(incident.progress * (incident.pourcentage / 100) for incident in sibling_incidents)
                print(parent_progress)
            
            
            if parent_tache.progress != parent_progress:
                parent_tache.progress = parent_progress
                parent_tache.save()
            
            parent_tache = parent_tache.tache_mere
            print(parent_tache)
        

        if parent_tache is None:
            projet = self.projet
            projet_taches = Tache.objects.filter(projet=projet,tache_mere=None)
            project_progress = sum(tache.progress * (tache.pourcentage / 100) for tache in projet_taches)
            
            print("Current Tache:", self)
            print("Total Progress:", total_progress)
            print("Project Progress:", project_progress)
            
            if projet.progress != project_progress:
                projet.progress = project_progress
                projet.save()
                print("Project Updated:", projet)
                        

class EtatTache(models.Model):
    id_check = models.AutoField(primary_key=True)
    date = models.DateField(default=datetime.now)
    tache_finis = models.BooleanField(blank=False,default=False)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE,related_name="checkTache")
    employe = models.ForeignKey("Employe",on_delete=models.CASCADE, related_name="checktaches")
    def __str__(self):
        return (f"l'état du tache "+self.tache.nom_tache)
    
    def save(self, *args, **kwargs):
        if self.tache_finis:  
            total_employees = self.tache.employe.all().count()
            if total_employees > 0:  
                progress_increment = 100 / total_employees
                self.tache.progress += progress_increment
                self.tache.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.tache_finis:
            total_employees = self.tache.employe.all().count()
            if total_employees > 0:
                progress_decrement = 100 / total_employees
                self.tache.progress -= progress_decrement
                self.tache.save()

        super().delete(*args, **kwargs)


class SuiviTache(models.Model):
    id_suivi = models.AutoField(primary_key=True)
    date_suivi = models.DateField(default=datetime.now)
    details = models.TextField()
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE,related_name="suiviTache")
    employe = models.ForeignKey(Employe,on_delete=models.CASCADE,related_name="suiviTache",null=True)
    def __str__(self):
        return (f"le suivi du tache "+self.tache.nom_tache)

class Document(models.Model):
    id_document = models.AutoField(primary_key=True)
    date = models.DateField(default=datetime.now)
    titre = models.CharField(max_length = 30)
    type = models.CharField(max_length = 30)
    doc = models.FileField(upload_to='pdfs/', default=None)
    details = models.TextField(null=True)
    projet = models.ForeignKey(Projet,on_delete=models.CASCADE)
    tache = models.ForeignKey(Tache, on_delete=models.CASCADE,null=True,blank=True,default = None)
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE)
    
    def __str__(self):
        return (self.titre)
    

class Ressource(models.Model):
    Type_ressource= (
     ('1', 'Matériel de Transport'),
     ('2', 'Matériel pour le Diagnostic'),
     ('3', 'Matériel pour le Mesure'),
     ('4', 'Matériel de Nettoyage'), 
     ('5', 'Matériel pour gros oeuvre'),
     ('6', 'Matériel pour second oeuvre'),
     ('7', 'Matériel pour Espace verts'),
     ('8', 'Matériel pour Industrie'),   
     ('9', 'Matériel de Manutention'),
     ('10','Matériel de Signalisation'),
     ('11','Matériel portatif'),
     ('12','Engins de Terrasement'),
     ('13','Machines à Projete'),
     ('14','Electricité sur chantiers'),
     ('15','Autre'),
     ) 
    
    Etat_ressource = (
        ('1', 'Bonne Etat'),
        ('2', 'Endomagé'),
        ('3', 'En Panne'),
     )

    Dispo_ressource = (
        ('1', 'Disponible'),
        ('2', 'Louer'),
        ('3', 'En Panne'),
    )
    
    id_ressource = models.AutoField(primary_key=True)
    lib_ressource =  models.CharField(max_length = 30)
    marque_ressource =  models.CharField(max_length = 30)
    code =  models.CharField(max_length = 30)
    type = models.CharField(max_length=2 ,choices=Type_ressource)
    etat = models.CharField(max_length=2 ,choices=Etat_ressource)
    disponibilite = models.CharField(max_length=2 ,choices=Dispo_ressource)
    def __str__(self):
        return (self.lib_ressource)
    def save(self, *args, **kwargs):
        if self.etat == '3':  
            self.disponibilite = '3'  
        super().save(*args, **kwargs)
    
class Comission(models.Model):
    Type_comission = (
        ('1', 'CME'),
        ('2', 'COP'),
        ('3', 'CEO'),
        )
    
    id_comission = models.AutoField(primary_key=True)
    titre = models.CharField(max_length=60)
    date = models.DateField(default= datetime.now)
    details = models.TextField()
    type = models.CharField(max_length=30 , choices = Type_comission)
    president = models.ForeignKey(Employe, on_delete=models.SET_NULL, null=True)
    employes = models.ManyToManyField("Employe", related_name="comissions",blank=True)
    projet = models.ForeignKey(Projet, on_delete=models.CASCADE, related_name="comissions")
    tache = models.ForeignKey(Tache,on_delete= models.SET_NULL, null = True,blank=True)
    PV = models.FileField(upload_to='pdfs/', default=None ,null = True,blank=True)
    def __str__(self):
        return (self.titre)
    
class UtilisationRessource(models.Model):
    id_TR= models.AutoField(primary_key=True)
    date_debut = models.DateField(default= datetime.now)
    date_fin = models.DateField(default= datetime.now)
    tache = models.ForeignKey(Tache,on_delete= models.CASCADE,related_name="util_ressource")
    ressource = models.ForeignKey(Ressource,on_delete= models.CASCADE,related_name="util_ressource")
    def __str__(self):
        return (self.tache.nom_tache+" - "+self.ressource.lib_ressource)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.ressource.disponibilite = '2'  
        self.ressource.save()  


