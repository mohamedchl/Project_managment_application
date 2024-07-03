from typing import Any
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpRequest
from .models import Projet, EtatProjet, Employe, Comission, Marchet, MaitreOuvrage, Tache, Incident, SuiviTache, SuiviIncident, Notification, UtilisationRessource, Ressource, Document,NotificationSeen,IncidentSeen, EtatTache
from django.contrib.auth.models import User
from django.contrib.admin import ModelAdmin
from django.db.models import Q,Sum
from django_select2.forms import ModelSelect2Widget
from .models import Projet
from django import forms
from .utils import get_current_request
from django_currentuser.middleware import get_current_authenticated_user
from django.utils.html import format_html
from django.forms.widgets import TextInput
from django.utils.html import format_html
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponseRedirect
from datetime import datetime




admin.site.site_header='Gestion de Projet'
admin.site.site_title='Gestion de Projet'

class ProgressInput(forms.TextInput):
    input_type = 'range'
    min_value = 0
    max_value = 100
    step = 1
    template_name = 'widgets/progress_input.html'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'progress-input', 'readonly': 'readonly'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
        self.context = self.get_context(name='', value=None, attrs=default_attrs)

    def format_value(self, value):
        if value is None:
            return ''
        return str(value)

class ProgressInputModifiable(forms.TextInput):
    input_type = 'range'
    min_value = 0
    max_value = 100
    step = 1
    template_name = 'widgets/progress_input_modifiable.html'

    def __init__(self, attrs=None):
        default_attrs = {'class': 'progress-input'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def format_value(self, value):
        if value is None:
            return ''
        return str(value)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = self.format_value(value)
        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        field_name = attrs.get('name', None)
        if field_name:
            attrs['oninput'] = f'updateProgressValue("{field_name}", this.value)'
        return attrs

class ProjectsWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            display_value = ""
        elif isinstance(value, QuerySet):
            display_value = '\n'.join([f"- {proj.nom_projet}\n" for proj in value])
        else:
            display_value = '\n'.join([f"- {v}\n" for v in value])
        return display_value
    
class EtatProjetForm(forms.ModelForm):
    class Meta:
        model = EtatProjet
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        if user and user.groups.filter(name='Chef de projet').exists():
            projets = Projet.objects.filter(chefProjet__email_employe=user.email)
            self.fields['projet'].queryset = projets

from django import forms
from .models import UtilisationRessource, Ressource, Tache
from django.db.models import Q

class UtilisationRessourceForm(forms.ModelForm):
    id_TR = forms.IntegerField(label='id',required=False, widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    class Meta:
        model = UtilisationRessource
        fields = ['id_TR', 'date_debut', 'date_fin', 'tache', 'ressource']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ressources = Ressource.objects.filter(Q(disponibilite='1')|Q(disponibilite='2'))
        self.fields['ressource'].queryset = ressources
        self.fields['tache'].widget.attrs.update({'class': 'normal-width'})
        request = get_current_request()
        user = request.user
        if user and user.groups.filter(name='Chef de projet').exists():
            taches = Tache.objects.filter(projet__chefProjet__email_employe=user.email)
            self.fields['tache'].queryset = taches
        
        # Make id_TR read-only and add it to the form fields if instance is not None
        if self.instance and self.instance.pk:
            self.fields['id_TR'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        ressource = cleaned_data.get('ressource')
        tache = cleaned_data.get('tache')
        projet = tache.projet if tache else None

        if date_debut and date_fin and date_debut > date_fin:
            self.add_error('date_debut', "La date début de l'utilisation ne doit pas être après la date fin !!")

        if date_debut and projet and date_debut < projet.date_debut:
            self.add_error('date_debut', f"La date début de l'utilisation ne peut pas être avant la date de début du projet {projet.nom_projet} qui est {projet.date_debut} .")

        if date_fin and projet and date_fin > projet.date_fin:
            self.add_error('date_fin', f"La date fin de l'utilisation ne peut pas être après la date de fin du projet {projet.nom_projet} qui est {projet.date_fin} .")

        if date_debut and date_fin and ressource:
            overlapping_utilisations = UtilisationRessource.objects.filter(
                ressource=ressource,
                date_debut__lt=date_fin,
                date_fin__gt=date_debut
            ).exclude(pk=self.instance.pk)

            if overlapping_utilisations.exists():
                self.add_error('date_debut', "Les dates sélectionnées se chevauchent avec une autre utilisation de cette ressource.")
                self.add_error('date_fin', "Les dates sélectionnées se chevauchent avec une autre utilisation de cette ressource.")
                
        return cleaned_data

          
class mOuvrageForm(forms.ModelForm):


    class Meta:
        model = EtatProjet
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
            

class RelatedProjectsWidget(forms.widgets.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            display_value = ""
        else:
            display_value = ', '.join(str(item) for item in value)
        return display_value

class EmployeProjetForm(forms.ModelForm):
    Projets = forms.CharField(widget=ProjectsWidget, required=False)
    Taches = forms.CharField(widget=ProjectsWidget, required=False)

    class Meta:
        model = Employe
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            projets = self.instance.projets.all()
            taches = self.instance.taches.all()

            # Set initial values for projects and tasks
            self.fields['Projets'].initial = projets
            self.fields['Taches'].initial = taches

            # Set widget attributes
            self.fields['Projets'].widget.attrs['readonly'] = True
            self.fields['Taches'].widget.attrs['readonly'] = True

class SuiviTacheForm(forms.ModelForm):
    class Meta:
        model = SuiviTache
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        if user and user.is_superuser:
            taches = Tache.objects.filter(type = '2')
            self.fields['tache'].queryset = taches
            
        elif user.groups.filter(name='Chef de projet').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            self.fields['employe'].widget.attrs['readonly'] = True
            taches = Tache.objects.filter(
                            Q(employe__email_employe=user.email, type='2') |
                            Q(projet__chefProjet__email_employe=user.email, type='2')
                        ).distinct()
            self.fields['tache'].queryset = taches
        elif request.user.groups.filter(name='Employe').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            self.fields['employe'].widget.attrs['readonly'] = True
            taches = Tache.objects.filter(Q(employe__email_employe=user.email,type = '2')|Q(chef_tache__email_employe=user.email,type= '2')).distinct()
            self.fields['tache'].queryset = taches

class SuiviIncidentForm(forms.ModelForm):
    class Meta:
        model = SuiviTache
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        if user and user.is_superuser:
            pass
        elif user.groups.filter(name='Chef de projet').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            print(employe)
            self.fields['employe'].widget.attrs['readonly'] = True
            incidents = Incident.objects.filter(projet__chefProjet__email_employe=user.email)
            self.fields['incident'].queryset = incidents
        elif request.user.groups.filter(name='Employe').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            self.fields['employe'].widget.attrs['readonly'] = True
            incidents = Incident.objects.filter(employe__email_employe=user.email)
            self.fields['incident'].queryset = incidents

class EmployeAdmin(admin.ModelAdmin):
    list_display = ['matricule', 'nom_employe', 'email_employe', 'bureau', 'poste']
    list_filter = ['bureau', 'poste','projets','taches']
    search_fields = ['nom_employe', 'matricule']
    form = EmployeProjetForm

    fieldsets = [
        ('Details', {
            'classes': ('',),
            'fields': ['matricule', 'nom_employe', 'bureau', 'email_employe', 'telephone',]}),
        ('Etat', {
            'classes': ('',),
            'fields': ['etat_employe', 'poste']

        }),
        ('Projets info', {
            'classes': ('',),
            'fields': ['display_projets', 'display_taches']

        }),

    ]
    readonly_fields = ['display_projets', 'display_taches']
    def display_projets(self, obj):
        # Join project names into separate lines with a hyphen before each
        return '\n'.join(f"- {projet.nom_projet}" for projet in obj.projets.all())

    def display_taches(self, obj):
        # Join task names into separate lines with a hyphen before each
        return '\n'.join(f"- {tache.nom_tache} (Projet : {tache.projet.nom_projet})" for tache in obj.taches.all())

    display_projets.short_description = 'Projets affecté'
    display_projets.allow_tags = True
    display_taches.short_description = 'Taches affecté'
    display_taches.allow_tags = True

    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return Employe.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            projets = Projet.objects.filter(chefProjet__email_employe=user_email)
            return Employe.objects.filter(projets__in=projets).distinct()
        else:
            return Employe.objects.none()

    

    def affecter_a_un_projet(self, request, queryset):
        if request.user.groups.filter(name='Chef de projet').exists():
            # If the user is in the "Chef de projet" group, show a message
            messages.error(request, "Vous n'avez pas la permession pour utiliser cette action .")
            return
        selected_employee_ids = ','.join(str(employee.id_employe) for employee in queryset)
        url = reverse('affecter_projet') + f'?employee_ids={selected_employee_ids}'
        return HttpResponseRedirect(url)
    
    def affecter_a_un_notification(self, request, queryset):
        selected_employee_ids = ','.join(str(employee.id_employe) for employee in queryset)
        url = reverse('affecter_notification') + f'?employee_ids={selected_employee_ids}'
        return HttpResponseRedirect(url)
    
    def affecter_a_un_tache(self, request, queryset):
        # Get selected employee IDs
        selected_employee_ids = ','.join(str(employee.id_employe) for employee in queryset)
        
        if request.user.groups.filter(name='Chef de projet').exists():
            # If the user is in the "Chef de projet" group, set project_ids to the projects where the user is the chefProjet
            project_ids = set(Projet.objects.filter(chefProjet__email_employe=request.user.email).values_list('id_projet', flat=True))
        else:
            # Otherwise, get project IDs for employees
            project_ids = set()
            for employee in queryset:
                project_ids.update(employee.projets.values_list('id_projet', flat=True))
        
        # Construct URL with employee IDs and project IDs
        url = reverse('affecter_tache') + f'?employee_ids={selected_employee_ids}&project_ids={",".join(str(pid) for pid in project_ids)}'
        
        return HttpResponseRedirect(url)
    
    def affecter_a_un_incident(self, request, queryset):
        # Get selected employee IDs
        selected_employee_ids = ','.join(str(employee.id_employe) for employee in queryset)
        
        if request.user.groups.filter(name='Chef de projet').exists():
            # If the user is in the "Chef de projet" group, set project_ids to the projects where the user is the chefProjet
            project_ids = set(Projet.objects.filter(chefProjet__email_employe=request.user.email).values_list('id_projet', flat=True))
        else:
            # Otherwise, get project IDs for employees
            project_ids = set()
            for employee in queryset:
                project_ids.update(employee.projets.values_list('id_projet', flat=True))
        
        # Construct URL with employee IDs and project IDs
        url = reverse('affecter_incident') + f'?employee_ids={selected_employee_ids}&project_ids={",".join(str(pid) for pid in project_ids)}'
        
        return HttpResponseRedirect(url)

    affecter_a_un_projet.short_description = "Affecter/retirer à un projet"
    affecter_a_un_notification.short_description = "Affecter/retirer à une notification"
    affecter_a_un_tache.short_description = "Affecter/retirer à une tache"
    affecter_a_un_incident.short_description = "Affecter/retirer à un incident"
    actions = [affecter_a_un_projet,affecter_a_un_tache,affecter_a_un_incident,affecter_a_un_notification]


class NotificationAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/admin.css',),
        }

    list_display = [
        'get_type_display',
        'titre',
        'date',
    ]
    fieldsets = [      
           ('Details', {
            'classes': ('',),
            'fields': ['type','titre','date','details','employe']}),
            ]
    
    readonly_fields=['employes_display']
    list_filter = ['type','date']
    search_fields = ['titre']
    
    def get_type_display(self, obj):
        type_icons = {
           '1': 'fas fa-info-circle',  # Information icon
            '2': 'fas fa-exclamation-triangle',  # Warning icon
            '3': 'fas fa-exclamation-circle',  # Error icon
        }
        type_color_class = {
            '1': 'info',
            '2': 'warning',
            '3': 'error',
        }.get(obj.type, '')  
        
        return format_html('<span class="{}"><i class="{}"></i>  {}</span>',type_color_class, type_icons.get(obj.type, ''),  obj.get_type_display())
    get_type_display.short_description = 'Type'  
    

    def employes_display(self, obj):
        return '\n'.join(f"- {employe.nom_employe} ({employe.get_poste_display()})" for employe in obj.employe.all())
    employes_display.short_description = 'Employés'


    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        user_email = request.user.email
        if request.user.groups.filter(name='Chef de projet').exists() or request.user.is_superuser:
            queryset= Notification.objects.all()
            
        elif request.user.groups.filter(name='Employe').exists():
            queryset= Notification.objects.filter(employe__email_employe=user_email)
            
            
        return queryset

        
class IncidentForm(forms.ModelForm):
    employe_display = forms.CharField(label='Employés', required=False, widget=forms.Textarea(attrs={'readonly': 'readonly', 'style': 'width: 100%; border: none; background-color: transparent;'}))
    class Meta:
        model = Incident
        fields = '__all__'
        widgets = {
            'agentDeclencheur': ModelSelect2Widget(model=Employe, search_fields=['nom_employe__icontains', 'matricule__icontains']),
            'progress': ProgressInputModifiable(attrs={'name': 'progress'}),  # Set ID for progress field
            'pourcentage': ProgressInputModifiable(attrs={'name': 'pourcentage'}),  # Set ID for pourcentage field
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        
        if user and user.groups.filter(name='Chef de projet').exists():
            projets = Projet.objects.filter(chefProjet__email_employe=user.email)
            instance = kwargs.get('instance')
            if instance and instance.projet in projets :
                self.fields['employe'].queryset = Employe.objects.filter(projets__in=projets).distinct()
            if self.instance.pk is None:  # This is a new instance, set defaults
                self.initial['progress'] = 0
                self.initial['pourcentage'] = 0
            else:  # Existing instance, ensure they are set to 0 if None
                if self.instance.progress is None:
                    self.instance.progress = 0
                if self.instance.pourcentage is None:
                    self.instance.pourcentage = 0
            if instance is not None:
                employe_associated = instance.employe.filter(email_employe=user.email).exists()
                employe_count = instance.employe.count()
                rows = max(1, employe_count)  
                self.fields['employe_display'].widget.attrs['rows'] = rows
                self.fields['employe_display'].initial = '\n'.join(
                f"- {employe.nom_employe} ({employe.get_poste_display()})" for employe in instance.employe.all()
                                                )
                if projets.exists() and not employe_associated:
                    projet = projets.first()
                    self.fields['projet'].queryset = projets
                    self.fields['projet'].initial = projet.nom_projet
                    self.fields['projet'].widget.attrs['readonly'] = True
                    
                    tache_queryset = Tache.objects.filter(projet__chefProjet__email_employe=user.email)
                    self.fields['tache'].queryset = tache_queryset
            else:
                projet = projets.first()
                self.fields['projet'].queryset = projets
                
                tache_queryset = Tache.objects.filter(projet__chefProjet__email_employe=user.email)
                self.fields['tache'].queryset = tache_queryset
        elif user.is_superuser:
            instance = kwargs.get('instance')
            if self.instance.progress is None:
                    self.instance.progress = 0
            if self.instance.pourcentage is None:
                    self.instance.pourcentage = 0

    def clean(self):
        cleaned_data = super().clean()
        projet = cleaned_data.get('projet')
        incident = self.instance
        tache = cleaned_data.get('tache')
        nom_incident = cleaned_data.get('nom_incident')
        if incident.pk is None:
            if nom_incident and projet and Incident.objects.filter(projet=projet,nom_incident=nom_incident):
                raise ValidationError(f"Un incident de nom {nom_incident} existe déja, le nom de l'incident doit etre unique dans le projet.")
        else:
            if nom_incident and projet and Incident.objects.filter(projet=projet,nom_incident=nom_incident).exclude(id_incident=incident.id_incident):
                raise ValidationError(f"Un incident de nom {nom_incident} existe déja, le nom de l'incident doit etre unique dans le projet.")
       
        pourcentage = cleaned_data.get('pourcentage')
        if tache and projet :
            total_percentage=0
            if Tache.objects.filter(tache_mere=tache, projet=projet).exists():
                total_percentage += Tache.objects.filter(tache_mere=tache, projet=projet).aggregate(total=Sum('pourcentage'))['total']
            if Incident.objects.filter(tache=tache).exclude(pk=incident.id_incident).exists():
                total_percentage += Incident.objects.filter(tache=tache).exclude(pk=incident.id_incident).aggregate(total=Sum('pourcentage'))['total']

            if total_percentage:
                pourcentage_accepte = 100 - total_percentage
                total_percentage += pourcentage

                if total_percentage > 100:
                    raise forms.ValidationError(f"le pourcentage total des sous-taches et incidents de tache {tache} doit etre 100% le pourcentage accepté est {pourcentage_accepte}%.")

        
        return cleaned_data
 
class IncidentAdmin(admin.ModelAdmin):
    form = IncidentForm
    list_display = ['get_nom_incident_display', 'date_incident','get_progress_display', 'agentDeclencheur','projet']
    list_filter = ['agentDeclencheur', 'date_incident','projet']  
    search_fields = ['nom_incident','projet__nom_projet']
    fieldsets = [      
           ('Details', {
            'classes': ('',),
            'fields': ['nom_incident','pourcentage','progress','tache','agentDeclencheur','details']}),
             
            ('Dates', {
            'classes': ('',),
            'fields': ['date_incident']}),
             
            ('Projet info', {
            'classes': ('',),
            'fields': ['projet','employe']}),  
              
               ]
    def get_progress_display(self, obj):
        return format_html('<span>{} %</span>',float("{:.3f}".format(obj.progress)))
    get_progress_display.short_description = 'progress' 
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return Incident.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            return Incident.objects.filter(Q(projet__chefProjet__email_employe=user_email) | Q(employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            return Incident.objects.filter(employe__email_employe=user_email)
        else:
            return Incident.objects.none()
        
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj) or ()

        if request.user.groups.filter(name="Chef de projet").exists() and obj is None:
            return ()  
    
        if request.user.groups.filter(name="Chef de projet").exists():
            if obj.projet not in Projet.objects.filter(chefProjet__email_employe=request.user.email) :
                readonly_fields +=('nom_incident','pourcentage','progress','date_incident','projet','tache','agentDeclencheur','details','employe')
        
        return readonly_fields
    def get_nom_incident_display (self, obj):
        request = get_current_request()
        if obj.projet in Projet.objects.filter(chefProjet__email_employe=request.user.email):
            return format_html('<span style="color: goldenrod;"><i class="fa fa-star"></i>{}</span>',  obj.nom_incident)
        else:
            return format_html('<span>{}</span>',  obj.nom_incident)
        
    get_nom_incident_display.short_description = 'Nom incident'

    from django.core.exceptions import ValidationError

    from django.contrib import messages

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and isinstance(obj, Incident):
            if request.user.groups.filter(name="Chef de projet").exists():
                if obj.projet.chefProjet.email_employe == request.user.email:
                    return True
                else:
                    return False
            elif request.user.groups.filter(name="Employe").exists():
                
                return False

        if request.POST and request.POST.get('action') == 'delete_selected':
            selected_incident_ids = request.POST.getlist('_selected_action')
            for incident_id in selected_incident_ids:
                try:
                    incident = Incident.objects.get(pk=incident_id)
                    if incident.projet.chefProjet.email_employe != request.user.email:
                        messages.error(request, f"Vous ne pouvez pas supprimer l'incident '{incident.nom_incident}' qui n'appartient pas à un projet que vous gérez. Veuillez retirer cet incident de votre sélection et réessayer.")
                        return False
                except Incident.DoesNotExist:
                    return False
            return True

        return True





    
   
    
class ProjetAdminForm(forms.ModelForm):

    class Meta:
        model = Projet
        fields = '__all__'
        widgets = {
            'chefProjet': ModelSelect2Widget(model=Employe, search_fields=['nom_employe__icontains', 'matricule__icontains']),
            'progress': ProgressInput(),
            'latest_etat': forms.TextInput(attrs={'readonly': True}),  # Set readonly attribute here in the widget
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        
                
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        projet_instance=self.instance
        print(date_debut,date_fin)
        no_errors = True
        if date_debut is not None and date_fin is not None:
            if date_debut >= date_fin or (date_fin - date_debut).days < 30:
                no_errors = False
                raise ValidationError("La durée du projet doit être plus de 30 jours.")
        
       

        return cleaned_data
    



class ProjetAdmin(admin.ModelAdmin):
    form = ProjetAdminForm
    list_display = ['get_nom_projet_display', 'get_etat_display', 'chefProjet', 'get_progress_display', 'maitreOuvrage']
    list_filter = ['date_debut', 'etat', 'chefProjet', 'maitreOuvrage','marchet']
    search_fields = ['nom_projet']
    fieldsets = [      
           ('Details', {
            'classes': ('',),
            'fields': ['nom_projet','details','chefProjet','maitreOuvrage','marchet']}),
             
            ('Dates', {
            'classes': ('',),
            'fields': ['date_debut','date_fin']}),
             
            ('Etat', {
            'classes': ('',),
            'fields': ['progress','latest_etat']}),  
            ('Employés', {
            'classes': ('',),
            'fields': ['employe']}),  
              
               ]
    readonly_fields = ['employes_display']
    def get_nom_projet_display (self, obj):
        request = get_current_request()
        if obj.chefProjet in Employe.objects.filter(email_employe=request.user.email):
            return format_html('<span style="color: goldenrod;"><i class="fa fa-star"></i>{}</span>',  obj.nom_projet)
        else:
            return format_html('<span>{}</span>',  obj.nom_projet)
        
    get_nom_projet_display.short_description = 'Nom projet'
    
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            queryset |= self.model.objects.filter(employe__nom_employe__icontains=search_term)
        return queryset, use_distinct

    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return Projet.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            return Projet.objects.filter(Q(chefProjet__email_employe=user_email) | Q(employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            return Projet.objects.filter(employe__email_employe=user_email)
        else:
            return Projet.objects.none()
    
    def employes_display(self, obj):
        return '\n'.join(f"- {employe.nom_employe} ({employe.get_poste_display()})" for employe in obj.employe.all())
    employes_display.short_description = 'Employés'  

    def get_progress_display(self, obj):
        return format_html('<span>{} %</span>',obj.progress)
    get_progress_display.short_description = 'progress'  
     
    def get_etat_display(self, obj):
        etat_instance = EtatProjet.objects.filter(projet=obj).last()
        if etat_instance:
            return f"{etat_instance.lib_etat}"
        return "No etat available"
    get_etat_display.short_description = 'etat'  



@login_required
def get_filtered_queryset(request):
    user_email = request.user.email
    if request.user.is_superuser:
        return Tache.objects.all()
    elif request.user.groups.filter(name='Chef de projet').exists():
        return Tache.objects.filter(Q(projet__chefProjet__email_employe=user_email) | Q(employe__email_employe=user_email)).distinct()
    elif request.user.groups.filter(name='Employe').exists():
        employe = Employe.objects.filter(email_employe=user_email).first()
        if employe and employe.poste == '12':
            return Tache.objects.filter(Q(chef_tache__email_employe=user_email)|Q(employe__email_employe=user_email)).distinct()
        elif employe:
            return Tache.objects.filter(employe__email_employe=user_email)
    else:
        return Tache.objects.none()


from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.contrib import messages
from .models import Tache, Incident, Projet, Employe

from .utils import get_current_request

class ChefProjetTacheForm(forms.ModelForm):

    class Meta:
        model = Tache
        fields = '__all__'
        widgets = {
            'progress': ProgressInputModifiable(attrs={'name': 'progress'}),
            'pourcentage': ProgressInputModifiable(attrs={'name': 'pourcentage'}),
        }

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        self.tache_mere_id = kwargs.pop('tache_mere_id', None)
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        instance = kwargs.get('instance')    

        if user.groups.filter(name='Chef de projet').exists():
            projets = Projet.objects.filter(chefProjet__email_employe=user.email)
            if instance:
                if instance.projet in projets: 
                    self.fields['employe'].queryset = Employe.objects.filter(projets__in=projets).distinct()
                    sousTache_queryset = Tache.objects.filter(projet__in=projets).exclude(pk=instance.pk)
                    self.fields['tache_mere'].queryset = sousTache_queryset
                    self.fields['chef_tache'].queryset = Employe.objects.filter(projets__in=projets).distinct()
            else:
                self.fields['projet'].queryset = projets
                self.fields['tache_mere'].queryset = Tache.objects.filter(projet__in=projets)
                self.fields['chef_tache'].queryset = Employe.objects.filter(projets__in=projets).distinct()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        nom_tache = cleaned_data.get('nom_tache')
        projet = cleaned_data.get('projet')
        tache = self.instance
        tache_mere = cleaned_data.get('tache_mere')
        type = cleaned_data.get('type')
        employe = cleaned_data.get('employe')
        chef_tache = cleaned_data.get('chef_tache')
        pourcentage = cleaned_data.get('pourcentage')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        request = get_current_request()

        if tache.pk is None:
            if nom_tache and projet and Tache.objects.filter(projet=projet, nom_tache=nom_tache).exists():
                raise ValidationError(f"Une tache de nom {nom_tache} existe déjà, le nom de tache doit être unique dans le projet.")
        else:
            if nom_tache and projet and Tache.objects.filter(projet=projet, nom_tache=nom_tache).exclude(id_tache=tache.id_tache).exists():
                raise ValidationError(f"Une tache de nom {nom_tache} existe déjà, le nom de tache doit être unique dans le projet.")
        if chef_tache:
            if chef_tache.poste == "11":
                raise ValidationError(f"Un chef de projet ne peut pas etre un chef de tache.")

        if projet:
            if date_debut and date_fin:
                if date_debut > date_fin:
                    raise ValidationError("La date de début de la tache doit être avant la date fin.")
                if date_debut < projet.date_debut:
                    raise ValidationError(f"La date debut de la tache ne peut pas être avant la date debut de projet qui est {projet.date_debut} !")
                if date_fin > projet.date_fin:
                    raise ValidationError(f"La date fin de la tache ne peut pas être après la date fin de projet qui est {projet.date_fin} !")
                if date_debut == date_fin:
                    raise ValidationError("La durée d'une tache doit être un jour minimum.")
            if tache_mere:
                if date_debut < tache_mere.date_debut:
                    raise ValidationError(f"La date debut de la tache ne peut pas être avant la date debut de tache mère qui est {tache_mere.date_debut} !")
                if date_fin > tache_mere.date_fin:
                    raise ValidationError(f"La date fin de la tache ne peut pas être après la date fin de tache mère qui est {tache_mere.date_fin} !")

        if tache_mere and tache:
            if projet != tache_mere.projet:
                raise ValidationError(f"La sous-tâche {tache} doit être dans le même projet que la tache mère {tache_mere}.")

        if tache_mere and tache_mere.type == '1':
            raise ValidationError("Une tache simple ne peut pas avoir des sous-taches.")

        if projet and employe:
            employe_list = employe.values_list('pk', flat=True) if employe else []
            if employe_list and not employe.filter(pk__in=projet.employe.all().values_list('pk', flat=True)).exists():
                raise ValidationError(f"L'employé {employe.first().nom_employe} n'est pas partie du projet {projet.nom_projet}.")

        total_percentage = 0
        if tache_mere and projet:
            total_percentage = Tache.objects.filter(tache_mere=tache_mere, projet=projet).exclude(pk=self.instance.pk).aggregate(total=Sum('pourcentage'))['total'] or 0
            if Incident.objects.filter(tache=tache_mere, projet=projet).exists():
                total_percentage += Incident.objects.filter(tache=tache_mere, projet=projet).aggregate(total=Sum('pourcentage'))['total'] or 0

        if total_percentage:
            pourcentage_accepte = 100 - total_percentage
            total_percentage += pourcentage
            if total_percentage > 100:
                if tache_mere is None:
                    raise ValidationError(f"Le pourcentage total des sous-taches de projet {projet} doit être 100%. Le pourcentage accepté est {pourcentage_accepte}%.")
                else:
                    raise ValidationError(f"Le pourcentage total des sous-taches de tache {tache_mere} doit être 100%. Le pourcentage accepté est {pourcentage_accepte}%.")

        if tache_mere is None:
            messages.warning(request, "La tache mère de cette tache est NULL ce qui signifie que cette tache est directement sous le projet.")

        return cleaned_data


def get_employe_display(instance):
    if instance:
        employe_list = [f"- {employe.nom_employe} ({employe.get_poste_display()})" for employe in instance.employe.all()]
        return '\n'.join(employe_list)
    else:
        return ''

from django import forms

class EmployeTacheForm(forms.ModelForm):
    class Meta:
        model = Tache
        fields = '__all__'
        widgets = {
            'progress': ProgressInput(),
            'pourcentage': ProgressInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')

    def clean(self):
        cleaned_data = super().clean()
        # No additional cleaning necessary for read-only form
        return cleaned_data


class TacheAdmin(admin.ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if request.user.groups.filter(name='Chef de projet').exists() or request.user.is_superuser:
            if obj is None and 'tache_mere_id' in form.base_fields:
                tache_mere_id = request.GET.get('tache_mere_id')
                if tache_mere_id:
                    form.base_fields['tache_mere'].widget = forms.HiddenInput()
                    form.base_fields['tache_mere'].initial = tache_mere_id

            kwargs['form'] = ChefProjetTacheForm

        else:
            kwargs['form'] = EmployeTacheForm
        return super().get_form(request, obj, **kwargs)
    
    list_display = ['get_nom_tache_display', 'date_debut', 'get_progress_display', 'projet','chef_tache']
    list_filter = ['projet', 'employe','date_debut','date_fin','type','chef_tache']
    search_fields = ['nom_tache']

   
    
    fieldsets = [
            ('Details', {
                'classes': ('',),
                'fields': ['nom_tache',  'pourcentage', 'progress','tache_mere', 'type', 'details']
            }),
            ('Dates', {
                'classes': ('',),
                'fields': ['date_debut', 'date_fin']
            }),
            ('Projet info', {
                'classes': ('',),
                'fields': ['projet', 'chef_tache', 'employe']
            }),
            
        ]

        
    def get_progress_display(self, obj):
        return format_html('<span>{} %</span>',float("{:.3f}".format(obj.progress)))
    get_progress_display.short_description = 'progress'  
    
    def get_queryset(self, request):
        return get_filtered_queryset(request)
    

    def get_nom_tache_display (self, obj):
        request = get_current_request()
        if obj.projet in Projet.objects.filter(chefProjet__email_employe=request.user.email):
            return format_html('<span style="color: goldenrod;"><i class="fa fa-star"></i>{}</span>',  obj.nom_tache)
        else:
            return format_html('<span>{}</span>',  obj.nom_tache)
        
    get_nom_tache_display.short_description = 'Nom tache'
    
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj=obj) or ()

        if request.user.groups.filter(name="Chef de projet").exists() and obj is None:
            return ('incidents','sous_tache')
            
        if request.user.groups.filter(name="Chef de projet").exists():
            if obj and obj.projet not in Projet.objects.filter(chefProjet__email_employe=request.user.email):
                readonly_fields += (
                    'nom_tache', 'pourcentage', 'progress', 'type', 'date_debut', 'date_fin',
                    'projet', 'employe', 'sous_tache', 'tache_mere', 'chef_tache', 'details','incidents'
                )
        if obj and obj.type == '1':
            readonly_fields += ('progress',)
        elif request.user.groups.filter(name="Employe").exists():
            readonly_fields = ()

        return readonly_fields

    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj and isinstance(obj, Tache):
            if request.user.groups.filter(name="Chef de projet").exists():
                if obj.projet.chefProjet.email_employe == request.user.email:
                    return True
                else:
                    return False
            elif request.user.groups.filter(name="Employe").exists():
                return False

        if request.POST and request.POST.get('action') == 'delete_selected':
            selected_task_ids = request.POST.getlist('_selected_action')
            for task_id in selected_task_ids:
                try:
                    task = Tache.objects.get(pk=task_id)
                    if task.projet.chefProjet.email_employe != request.user.email:
                        messages.error(request, f"Vous ne pouvez pas supprimer la tâche '{task.nom_tache}' qui n'appartient pas à un projet que vous gérez. Veuillez retirer cette tâche de votre sélection et réessayer.")
                        return False
                except Tache.DoesNotExist:
                    return False
            return True

        return True




class EtatProjetAdmin(admin.ModelAdmin):
    list_display = ['lib_etat', 'date_etat', 'projet']
    list_filter = ['date_etat','projet']
    search_fields = ['lib_etat']
    
    form = EtatProjetForm
    fieldsets = [
       
           ('Details', {
            'classes': ('',),
            'fields': ['lib_etat', 'date_etat', 'projet']}),]
    
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return EtatProjet.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            # Filter EtatProjet objects where the projet's chefProjet or employe's email matches the current user's email
            return EtatProjet.objects.filter(Q(projet__chefProjet__email_employe=user_email) | Q(projet__employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            # Filter EtatProjet objects where the employe's email matches the current user's email
            return EtatProjet.objects.filter(projet__employe__email_employe=user_email)
        else:
            # If the user doesn't have any specific permissions, return an empty queryset
            return EtatProjet.objects.none()


   
class MaitreOuvrageAdmin(admin.ModelAdmin):
    list_display = ['lib_mouvrage', 'details']
    list_filter = ['projet']
    search_fields = ['lib_mouvrage']
    
    form = mOuvrageForm
    fieldsets = [
       
           ('Details', {
            'classes': ('',),
            'fields': ['lib_mouvrage','details']}),]

class ComissionForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = '__all__'
        widgets={
            'president': ModelSelect2Widget(model=Employe, search_fields=['nom_employe__icontains', 'matricule__icontains']),
            #'employes': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        if user and user.groups.filter(name='Chef de projet').exists():
            projets = Projet.objects.filter(chefProjet__email_employe=user.email)
            if projets.exists():
                projet = projets.first()
                self.fields['projet'].queryset = projets
                self.fields['projet'].initial = projet.nom_projet
                self.fields['projet'].widget.attrs['readonly'] = True
                taches_queryset = Tache.objects.filter(projet=projet)
                self.fields['tache'].queryset = taches_queryset
                employes_queryset = Employe.objects.filter(projets=projet)
                self.fields['employes'].queryset = employes_queryset
    def clean(self):
        cleaned_data = super().clean()
        projet = cleaned_data.get('projet')
        tache = cleaned_data.get('tache')
        date = cleaned_data.get('date')
        
        if projet and tache and tache.projet != projet:
            raise ValidationError("La tâche sélectionnée ne fait pas partie du projet sélectionné.")
        if date and projet:
            if date<projet.date_debut:
                raise ValidationError(f"La date de commission ne peut pas etre avant la date de debut du projet {projet.nom_projet} qui est {projet.date_debut} .")
            elif date>projet.date_fin:
                raise ValidationError(f"La date de commission ne peut pas etre après la date de fin du projet {projet.nom_projet} qui est {projet.date_fin} .")
        
        return cleaned_data
 
class ComissionAdmin(admin.ModelAdmin):
    list_display = ['titre','date','type','projet','president']
    list_filter = ['projet','date','type','tache','employes']
    search_fields = ['titre']
    
    form = ComissionForm
    fieldsets = [
       
           ('Details', {
            'classes': ('',),
            'fields': ['type','details','titre','PV']}
            ),
           ('Date', {
            'classes': ('',),
            'fields': ['date']}
            ),
           ('Employés', {
            'classes': ('',),
            'fields': ['president','employes']}
            ),
           ('Projets info', {
            'classes': ('',),
            'fields': ['projet','tache']}
            ),
            
            
            ]
    def get_queryset(self, request):
        user_email = request.user.email
        employe=Employe.objects.filter(email_employe=user_email)
        if request.user.is_superuser:
            return Comission.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            # Filter EtatProjet objects where the projet's chefProjet or employe's email matches the current user's email
            return Comission.objects.filter(Q(projet__chefProjet__email_employe=user_email) | Q(projet__employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            # Filter EtatProjet objects where the employe's email matches the current user's email
            return Comission.objects.filter(projet__employe__email_employe=user_email)
        else:
            # If the user doesn't have any specific permissions, return an empty queryset
            return Comission.objects.none()
    
class DocumentForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = '__all__'
        
    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        
        if user:
            if user.groups.filter(name='Chef de projet').exists():
                employe = Employe.objects.filter(email_employe=user.email)
                self.fields['employe'].queryset = employe

                projets = Projet.objects.filter(chefProjet__email_employe=user.email) | Projet.objects.filter(employe__email_employe=user.email)
                if projets.exists():
                    self.fields['projet'].queryset = projets
                taches = Tache.objects.filter(projet__chefProjet__email_employe=user.email) | Tache.objects.filter(employe__email_employe = user.email)
                if taches.exists():
                    self.fields['tache'].queryset = taches
            elif user.groups.filter(name='Employe').exists():
                employe = Employe.objects.filter(email_employe=user.email)
                self.fields['employe'].queryset = employe
                self.fields['projet'].queryset = Projet.objects.filter(employe__email_employe=user.email)
                self.fields['tache'].queryset = Tache.objects.filter(employe__email_employe = user.email)
            


    def clean(self):
        cleaned_data = super().clean()
        projet = cleaned_data.get('projet')
        tache = cleaned_data.get('tache')
        date = cleaned_data.get('date')


        if projet and tache and tache.projet != projet:
            raise ValidationError("La tâche sélectionnée ne fait pas partie du projet sélectionné.")
        if projet and date:
            if date<projet.date_debut:
                raise ValidationError(f"La date de document ne peut pas etre avant la date de debut du projet {projet.nom_projet} qui est {projet.date_debut} .")
            elif date>projet.date_fin:
                raise ValidationError(f"La date de document ne peut pas etre après la date de fin du projet {projet.nom_projet} qui est {projet.date_fin} .")



        return cleaned_data
                    

class AdminDocument(admin.ModelAdmin):
    fieldsets = [
           ('Details', {
            'classes': ('',),
            'fields': ['type','titre','doc','details']}),
           ('Date', {
            'classes': ('',),
            'fields': ['date']}),
           ('Projet infos', {
            'classes': ('',),
            'fields': ['projet','tache','employe']}),]
    list_display = ('titre','type','doc','projet','employe','tache')
    list_filter = ['type','projet', 'tache','employe']  
    search_fields = ['titre',]
    form = DocumentForm
   
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return Document.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            # Filter EtatProjet objects where the projet's chefProjet or employe's email matches the current user's email
            return Document.objects.filter(Q(projet__chefProjet__email_employe=user_email) | Q(employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            # Filter EtatProjet objects where the employe's email matches the current user's email
            return Document.objects.filter(employe__email_employe=user_email)
        else:
            # If the user doesn't have any specific permissions, return an empty queryset
            return Comission.objects.none()

class AdminRessource(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/admin.css',),
        }
    fieldsets = [
           ('Details', {
            'classes': ('',),
            'fields': ['lib_ressource','marque_ressource','code','type']}),
           ('Etat', {
            'classes': ('',),
            'fields': ['etat','disponibilite']}),
            
            
            ]
    list_display = ('get_lib_display','marque_ressource','type','etat','disponibilite')
    list_filter = ['marque_ressource','type', 'disponibilite','etat']  
    search_fields = ['lib_ressource','code',]
    def get_lib_display(self, obj):
        type_color_class = {
            '1': 'success',
            '2': 'warning',
            '3': 'error',
        }.get(obj.disponibilite, '')  
        
        return format_html('<span class="{}">{}</span>',type_color_class,  obj.lib_ressource)
    get_lib_display.short_description = 'lib_ressource'

    def get_queryset(self, request):
        return super().get_queryset(request)

class AdminUtilisationRessource(admin.ModelAdmin):
    fieldsets = [
           ('Details', {
            'classes': ('',),
            'fields': ['id_TR','tache','ressource']}),
           ('Dates', {
            'classes': ('',),
            'fields': ['date_debut','date_fin']}),]
    list_display = ('tache', 'ressource', 'date_debut', 'date_fin')
    list_filter = ['date_debut', 'date_fin','tache', 'tache__projet','ressource', 'ressource__type']  
    search_fields = ['tache__nom_tache', 'ressource__lib_ressource']
    form = UtilisationRessourceForm
    class Media:
        css = {
            'all': ('css/admin.css',)
        }
        js = ('js/custom_admin.js',)
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return UtilisationRessource.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
           
            return UtilisationRessource.objects.filter(tache__projet__chefProjet__email_employe=user_email)
        else:
            return UtilisationRessource.objects.none()
        
from django.db.models import Case, When, Value, IntegerField, Q, F
class AdminSuiviTache(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/admin.css',),
        }
    fieldsets = [
           ('Date', {
            'classes': ('',),
            'fields': ['date_suivi']}),
           ('Details', {
            'classes': ('',),
            'fields': ['details','employe','tache']}),
            ]
    list_display = ('get_tache_display','date_suivi','employe')
    list_filter = ['date_suivi','tache','employe','tache__projet']  
    search_fields = ['tache','employe']
    form = SuiviTacheForm
    
   
    def get_tache_display (self, obj):
        if obj.tache.chef_tache == obj.employe:
            return format_html('<span style="color: goldenrod;"><i class="fa fa-star"></i> Le Suivi de la tache " {} " de chef de tache</span>',  obj.tache)
        else:
            return format_html('<span>Le Suivi de la tache " {} "</span>',  obj.tache)
    get_tache_display.short_description = 'Suivi tache'

    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return SuiviTache.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            return SuiviTache.objects.filter(Q(tache__projet__chefProjet__email_employe=user_email)|Q(employe__email_employe=user_email))
        elif request.user.groups.filter(name='Employe').exists():
            
            employe = Employe.objects.filter(email_employe=user_email).first()  # Get the first instance of Employe
            if employe and employe.poste == '12':  # Check if employe is not None before accessing poste
                return SuiviTache.objects.filter(tache__chef_tache__email_employe=user_email)
                
            return SuiviTache.objects.filter(employe__email_employe=user_email)
        return SuiviTache.objects.none()  # Return an empty queryset if none of the conditions are met 



class AdminSuiviIncident(admin.ModelAdmin):
    fieldsets = [
           ('Date', {
            'classes': ('',),
            'fields': ['date_suivi']}),
           ('Details', {
            'classes': ('',),
            'fields': ['details','employe','incident']}),
            ]
    list_display = ('get_incident_display','date_suivi','employe')
    list_filter = ['date_suivi','incident','incident__projet']  
    search_fields = ['tache','employe']
    form = SuiviIncidentForm

    
    def get_incident_display (self, obj):
        return format_html('<span>Le Suivi de lincident "{}"</span>',  obj.incident)
    get_incident_display.short_description = 'Suivi incident'
    
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return SuiviIncident.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            return SuiviIncident.objects.filter(Q(incident__projet__chefProjet__email_employe=user_email)|Q(employe__email_employe=user_email))
        elif request.user.groups.filter(name='Employe').exists():
            return SuiviIncident.objects.filter(employe__email_employe=user_email)
        else:
            return SuiviIncident.objects.none()

class EtatTacheForm(forms.ModelForm):
    class Meta:
        model = EtatTache  
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = get_current_request()
        user = request.user
        if user and user.is_superuser:
            taches = Tache.objects.filter(type='1')
            self.fields['tache'].queryset = taches
        elif user.groups.filter(name='Chef de projet').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            self.fields['employe'].widget.attrs['readonly'] = True
            taches = Tache.objects.filter(Q(projet__chefProjet__email_employe=user.email,type='1')|Q(employe__email_employe=user.email,type='1')).distinct()
            self.fields['tache'].queryset = taches
        elif request.user.groups.filter(name='Employe').exists():
            employe = Employe.objects.filter(email_employe=user.email)
            self.fields['employe'].queryset = employe
            self.fields['employe'].widget.attrs['readonly'] = True
            taches = Tache.objects.filter(employe__email_employe=user.email,type='1')
            self.fields['tache'].queryset = taches
    
    def clean(self):
        cleaned_data = super().clean()
        employe = cleaned_data.get('employe')
        tache = cleaned_data.get('tache')
        
        # Check if both employe and tache are not None
        if employe and tache:
            # Retrieve the queryset of employees associated with the task
            task_employees = tache.employe.all()
            # Check if the selected employee is not part of the task employees
            if employe not in task_employees:
                raise ValidationError("Vous ne pouvez pas cocher une tâche à laquelle vous ne participez pas !")
            if self.instance.pk is None:
                if EtatTache.objects.filter(tache=tache,employe=employe).exists():
                    raise ValidationError("Vous ne pouvez pas déclarer la fin de meme tache plusieurs fois! vous pouvez modifier l'état de tache")

        
        
        return cleaned_data

  
class AdminEtatTache(admin.ModelAdmin):
    fieldsets = [
           ('Date', {
            'classes': ('',),
            'fields': ['date']}),
           ('Details', {
            'classes': ('',),
            'fields': ['tache','tache_finis','employe']}),
            ]
    list_display = ('get_tache_display','employe','date','tache_finis')
    list_filter = ['date','tache','tache__projet','employe']  
    search_fields = ['tache','employe']
    form = EtatTacheForm

    
    def get_tache_display (self, obj):
        return format_html('<span>Etat du tache {}</span>',  obj.tache)
    
    get_tache_display.short_description = 'Etat du tache'

    
    def get_queryset(self, request):
        user_email = request.user.email
        if request.user.is_superuser:
            return EtatTache.objects.all()
        elif request.user.groups.filter(name='Chef de projet').exists():
            return EtatTache.objects.filter(Q(tache__projet__chefProjet__email_employe=user_email) | Q(employe__email_employe=user_email)).distinct()
        elif request.user.groups.filter(name='Employe').exists():
            return EtatTache.objects.filter(employe__email_employe=user_email)
        else:
            return EtatTache.objects.none()

class AdminMarchet(admin.ModelAdmin):
    fieldsets = [
           ('Details', {
            'classes': ('',),
            'fields': ['lib_marchet','details']}),
            ]
    list_display = ('id_marchet','lib_marchet')
    list_filter = ['lib_marchet','projet']  
    search_fields = ['lib_marchet']


class CustomAdminSite(admin.AdminSite):
    def index(self, request, extra_context=None):
        # Remove recent actions
        extra_context = extra_context or {}
        extra_context['recent_actions'] = []
        return super().index(request, extra_context)


custom_admin_site = CustomAdminSite(name='customadmin')
admin.site.register(Projet,ProjetAdmin)
admin.site.register(EtatProjet,EtatProjetAdmin)
admin.site.register(Comission,ComissionAdmin)
admin.site.register(Marchet,AdminMarchet)
admin.site.register(MaitreOuvrage,MaitreOuvrageAdmin)
admin.site.register(Tache,TacheAdmin)
admin.site.register(Incident,IncidentAdmin)
admin.site.register(SuiviTache,AdminSuiviTache)
admin.site.register(SuiviIncident,AdminSuiviIncident)
admin.site.register(Notification,NotificationAdmin)
admin.site.register(UtilisationRessource,AdminUtilisationRessource)
admin.site.register(Ressource,AdminRessource)
admin.site.register(Document,AdminDocument)
admin.site.register(NotificationSeen)
admin.site.register(IncidentSeen)
admin.site.unregister(User) 
admin.site.register(User, UserAdmin) 
admin.site.register(Employe, EmployeAdmin)  
admin.site.register(EtatTache,AdminEtatTache)