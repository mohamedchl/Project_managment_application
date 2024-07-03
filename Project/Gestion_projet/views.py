from django.shortcuts import render, redirect
from .forms import EmployeRegistrationForm,ProjetNameForm
from .models import Employe,Projet,Notification,NotificationSeen,Tache,Incident,Comission,Document,UtilisationRessource,Ressource,EtatProjet
from django.urls import reverse

def employe_registration_view(request):
    success_message = None
    username =None
    if request.method == 'POST':
        form = EmployeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            success_message = True
            employe = Employe.objects.filter(matricule=form.cleaned_data['matricule']).first()
            username = f"{employe.nom_employe.split()[0]}{employe.matricule}" 
    else:
        form = EmployeRegistrationForm()

    return render(
        request,
        'employe_registration.html',
        {'form': form, 'success_message': success_message,'username':username}
    )


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from .models import NotificationSeen,IncidentSeen


@login_required
def notification_count_api(request):
    try:
        admin = User.objects.get(username='admin')
        nbr_notif = NotificationSeen.objects.filter(user=request.user, seen=False).count()
        nbr_incident = IncidentSeen.objects.filter(user=request.user, seen=False).count()

        if request.user == admin :
            return JsonResponse({'nbr_notif': nbr_notif, 'nbr_incident': nbr_incident})
        else:
            employe = Employe.objects.get(email_employe=request.user.email)
            # Count the number of NotificationSeen instances where seen is False for the employe
            

            # Update the notificationNotSeen attribute of the employe
            employe.notificationNotSeen = nbr_notif
            employe.incidentNotSeen = nbr_incident
            employe.save()  # Save the employe instance to persist the changes

            return JsonResponse({'nbr_notif': nbr_notif, 'nbr_incident': nbr_incident})
    except Employe.DoesNotExist:
        return JsonResponse({'error': 'Employe not found'}, status=404)

from django.http import JsonResponse
from .models import NotificationSeen

def mark_notifications_seen(request):
    if request.user.is_authenticated:
        try:
            # Mark all NotificationSeen objects as seen for the current user
            NotificationSeen.objects.filter(user=request.user).update(seen=True)
            return JsonResponse({'success': True})
        except AttributeError:
            return JsonResponse({'error': 'User not authenticated'}, status=401)
    else:
        return JsonResponse({'error': 'User not authenticated'}, status=401)

def mark_incidents_seen(request):
    if request.user.is_authenticated:
        try:
            # Mark all IncidentSeen objects as seen for the current user
            IncidentSeen.objects.filter(user=request.user).update(seen=True)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    

def check_user_is_employee(request):
    is_employee = False
    if not request.user.groups.filter(name='Chef de projet').exists() and not request.user.is_superuser:
        is_employee = True
    return JsonResponse({'is_employee': is_employee})


from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Projet, Employe
def affecter_projet(request):
    projects = Projet.objects.all()[::-1]
    employee_idss = request.GET.get('employee_ids')
    employee_ids = request.GET.get('employee_ids').split(',')
    query = request.GET.get('q')
    if query:
        projects = Projet.objects.filter(nom_projet__icontains=query)
        employee_ids = request.GET.get('employee_ids').split('%2C')
        employee_ids = request.GET.get('employee_ids').split(',')

    # Handle project selection and employee association
    if request.method == 'POST':
        selected_project_ids = request.POST.getlist('selected_projects')
        if selected_project_ids and employee_ids:
            selected_employees = Employe.objects.filter(id_employe__in=employee_ids)
           
            if "Affecter" in request.POST:
                for project_id in selected_project_ids:
                    project = Projet.objects.get(id_projet=project_id)
                    notification = Notification.objects.create(
                        type='2',
                        titre=f'Affectation a projet "{project.nom_projet}"',
                        details=f'Cher(s) employé(s), Nous avons le plaisir de vous informer que vous avez été affecté(e)(s) au projet {project.nom_projet} géré par le chef "{project.chefProjet.nom_employe}". Votre expertise et votre contribution seront précieuses pour atteindre nos objectifs communs. Nous sommes impatients de travailler avec vous sur ce projet passionnant.'
                    )
                    for employe in selected_employees:
                        if Employe.objects.filter(id_employe=employe.id_employe, projets=project).exists():
                            messages.warning(request, f"L'employé {employe.nom_employe} est déjà dans le projet {project.nom_projet}")
                        else:
                            project.employe.add(employe)
                            notification.employe.add(employe)
                            user = User.objects.filter(email=employe.email_employe).first()
                            if user:
                                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                            employe.notificationNotSeen += 1
                            employe.save()
                            messages.success(request, f"L'employé {employe.nom_employe} est affecté au projet {project.nom_projet}")
                    notification.save()

            elif "Désaffecter" in request.POST:
                for project_id in selected_project_ids:
                    project = Projet.objects.get(id_projet=project_id)
                    for employe in selected_employees:
                        if not Employe.objects.filter(id_employe=employe.id_employe, projets=project).exists():
                            messages.warning(request, f"L'employé {employe.nom_employe} n'est pas affecté au projet {project.nom_projet}")
                        else:
                            project.employe.remove(employe)
                            messages.success(request, f"L'employé {employe.nom_employe} est retiré du projet {project.nom_projet}")

        return redirect('/admin/Gestion_projet/employe') 

    return render(request, 'affecter_projet.html', {'projects': projects, 'employee_ids': employee_idss})


def affecter_notification(request):
    notifications = Notification.objects.all()[::-1]
    
    employee_idss = request.GET.get('employee_ids')
    employee_ids = request.GET.get('employee_ids').split(',')

    query = request.GET.get('q')
    if query:
        notifications = Notification.objects.filter(titre__icontains=query)
        employee_ids = request.GET.get('employee_ids').split('%2C')
        employee_ids = request.GET.get('employee_ids').split(',')

    # Handle notification selection and employee association
    if request.method == 'POST':
        selected_notification_ids = request.POST.getlist('selected_notifications')
        
        if selected_notification_ids and employee_ids:
            selected_employees = Employe.objects.filter(id_employe__in=employee_ids)
            
            if "Affecter" in request.POST:
                for notification_id in selected_notification_ids:
                    notification = Notification.objects.get(id_notification=notification_id)
                    for employe in selected_employees:
                        if Employe.objects.filter(id_employe=employe.id_employe, notifications=notification).exists():
                            messages.warning(request, f"L'employé '{employe.nom_employe}' est déjà affecté dans la notification '{notification.titre}'")
                        else:
                            user = User.objects.filter(email=employe.email_employe).first()
                            NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                            employe.notificationNotSeen += 1
                            employe.save()
                            notification.employe.add(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement affecté dans la notification '{notification.titre}'")

            elif "Désaffecter" in request.POST:
                for notification_id in selected_notification_ids:
                    notification = Notification.objects.get(id_notification=notification_id)
                    for employe in selected_employees:
                        if not Employe.objects.filter(id_employe=employe.id_employe, notifications=notification).exists():
                            messages.warning(request, f"L'employé '{employe.nom_employe}' n'est pas affecté dans la notification '{notification.titre}'")
                        else:
                            user = User.objects.filter(email=employe.email_employe).first()
                            notification_notseen = NotificationSeen.objects.filter(user=user, notification=notification)
                            if notification_notseen.exists():
                                notification_notseen.delete()
                            notification.employe.remove(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement retiré de la notification '{notification.titre}'")

            return redirect('/admin/Gestion_projet/employe')

    return render(request, 'affecter_notification.html', {'notifications': notifications, 'employee_ids': employee_idss})

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from .models import Tache, Employe, Notification, NotificationSeen, User
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Tache, Employe, User

def affecter_tache(request):
    projets_ids = request.GET.get('project_ids')

    if projets_ids is None:
        taches = Tache.objects.none()
    else:
        projets_ids = projets_ids.split(',')
        taches = Tache.objects.filter(projet__in=projets_ids)[::-1]

    employee_idss = request.GET.get('employee_ids')
    employee_ids = request.GET.get('employee_ids').split(',')

    query = request.GET.get('q')
    if query:
        taches = Tache.objects.filter(nom_tache__icontains=query)
        employee_ids = request.GET.get('employee_ids').split('%2C')
        employee_ids = request.GET.get('employee_ids').split(',')

    if request.method == 'POST':
        selected_tache_ids = request.POST.getlist('selected_taches')

        if selected_tache_ids and employee_ids:
            selected_employees = Employe.objects.filter(id_employe__in=employee_ids)

            if "Affecter" in request.POST:
                for tache_id in selected_tache_ids:
                    tache = Tache.objects.get(id_tache=tache_id)
                    for employe in selected_employees:
                        if tache.employe.filter(id_employe=employe.id_employe).exists():
                            messages.warning(request, f"L'employé '{employe.nom_employe}' est déjà dans la tâche '{tache.nom_tache}'")
                        elif tache.projet not in employe.projets.all():
                            messages.error(request, f"L'employé '{employe.nom_employe}' n'est pas dans le projet '{tache.projet.nom_projet}' qui a la tâche '{tache.nom_tache}'")
                        else:
                            tache.employe.add(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement affecté à la tâche '{tache.nom_tache}'")

            elif "Désaffecter" in request.POST:
                for tache_id in selected_tache_ids:
                    tache = Tache.objects.get(id_tache=tache_id)
                    for employe in selected_employees:
                        if tache.projet not in employe.projets.all():
                            messages.error(request, f"L'employé {employe.nom_employe} n'est pas dans le projet {tache.projet.nom_projet} qui a la tâche {tache.nom_tache}")
                        elif not tache.employe.filter(id_employe=employe.id_employe).exists():
                            messages.warning(request, f"L'employé {employe.nom_employe} n'est déjà pas dans la tâche {tache.nom_tache}")
                        else:
                            try:
                                notification = Notification.objects.get(
                                    titre=f"Affectation à la tâche '{tache.nom_tache}' du projet {tache.projet.nom_projet}", 
                                    employe=employe
                                )
                                notification.employe.remove(employe)
                                notification.save()
                            except ObjectDoesNotExist:
                                pass
                            tache.employe.remove(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement retiré de la tâche '{tache.nom_tache}'")

            return redirect('/admin/Gestion_projet/employe')

    return render(request, 'affecter_tache.html', {'taches': taches, 'employee_ids': employee_idss})


from django.db.models import Q
from django.shortcuts import redirect, render
from django.contrib import messages
from django.db.models import Q
from .models import Incident, Employe, User, Notification, NotificationSeen, IncidentSeen

def affecter_incident(request):
    projets_ids = request.GET.get('project_ids')
    
    if projets_ids is None:
        incidents = Incident.objects.none()
    else:
        projets_ids = projets_ids.split(',')
        incidents = Incident.objects.filter(projet__in=projets_ids)[::-1]
        
    employee_idss = request.GET.get('employee_ids')
    employee_ids = request.GET.get('employee_ids').split(',')
    query = request.GET.get('q')
    if query:
        incidents = Incident.objects.filter(nom_incident__icontains=query)
        employee_ids = request.GET.get('employee_ids').split('%2C')
        employee_ids = request.GET.get('employee_ids').split(',')

    if request.method == 'POST':
        selected_incident_ids = request.POST.getlist('selected_incidents')
        if selected_incident_ids and employee_ids:
            selected_employees = Employe.objects.filter(id_employe__in=employee_ids)
            
            if "Affecter" in request.POST:
                for incident_id in selected_incident_ids:
                    incident = Incident.objects.get(id_incident=incident_id)
                    for employe in selected_employees:
                        if incident.employe.filter(id_employe=employe.id_employe).exists():
                            messages.warning(request, f"L'employé '{employe.nom_employe}' est déjà affecté à l'incident '{incident.nom_incident}'")
                        elif incident.projet not in employe.projets.all():
                            messages.error(request, f"L'employé '{employe.nom_employe}' n'est pas dans le projet '{incident.projet.nom_projet}' qui a l'incident '{incident.nom_incident}'")
                        else:
                            incident.employe.add(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement affecté à l'incident '{incident.nom_incident}'")
                
            elif "Désaffecter" in request.POST:
                for incident_id in selected_incident_ids:
                    incident = Incident.objects.get(id_incident=incident_id)
                    for employe in selected_employees:
                        if incident.projet not in employe.projets.all():
                            messages.error(request, f"L'employé {employe.nom_employe} n'est pas dans le projet {incident.projet.nom_projet} qui a l'incident {incident.nom_incident}")
                        elif not incident.employe.filter(id_employe=employe.id_employe).exists():
                            messages.warning(request, f"L'employé {employe.nom_employe} n'est déjà pas affecté à l'incident {incident.nom_incident}")
                        else:
                            incident.employe.remove(employe)
                            messages.success(request, f"L'employé '{employe.nom_employe}' est successivement retiré de l'incident '{incident.nom_incident}'")

            return redirect('/admin/Gestion_projet/employe')

    return render(request, 'affecter_incident.html', {'incidents': incidents, 'employee_ids': employee_idss})

from django.shortcuts import render
from django.utils import timezone
from .forms import ProjetNameForm,ProjetNameForm2,TacheNameForm
from .models import Projet,MaitreOuvrage
from collections import defaultdict
from datetime import timedelta
from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404
from fuzzywuzzy import process
from datetime import datetime


def projet_dashboard(request):
    form = ProjetNameForm(request.POST or None)
    form_valid = False
    message=None
    projet =None
    avancement = None
    avnc_color = None
    progressParJour=None
    dateF= None
    dif_jour = None
    projet_pas_commence=None
    chef_projet_un_projet=False
    user_is_admin = False
    user_is_chefProjet=False
    taches = None
    count_tache = None
    projet_non_finis=None
    nbr_projets=None
    document_exist=True
    comission_exist=True
    employe_exist=True
    tache_exist=True


    type_tache = ['Tâche simple','Tâche besoin d un suivi']
    count_type_tache=[]

    duree_tache=['de 1 jour à 10','de 10 jours à 1 mois','plus d un mois']
    count_duree_tache=[]

    type_employe_tache=['moin de 25','de 25 à 50','de 50 à 75','de 75 à 100', 'plus de 100']
    count_employe_tache=[]

    type_progress_tache=['de 0% de 25%','de 25% à 50%','de 50% à 75%','de 75% à 100%']
    count_progress_tache=[]

    type_soustache_tache=['pas des sous-taches','de 1 à 5','plus de 5']
    count_soustache_tache=[]

    type_incident_tache=['pas des incidents','de 1 à 5','plus de 5']
    count_incident_tache=[]
    
    dates_commission = []
    count_dates_commission = []

    type_commission=['CME','COP','CEO']
    count_type_commission = []

    dates_document = []
    count_dates_document = []

    type_document=[]
    count_type_document = []

    poste_employe = ['President Directeur Générale', 'Directeur Générale','Assistant','Consultant', 'Chef Stucture','Ingénieur d informatique', 'Ingénieur D Etudes','Chargé D Etudes ', 'Exploitant ', 'Ingénieur de Génie Civile ','Chef Projet', 'Chef Tache','Autre']
    count_poste_employe=[]

    etat_employe = ['Célibataire','Mariée']
    count_etat_employe = []

    nbr_tache = ['pas de taches associé','de 1 tache à 5','plus de 5 taches']
    count_nbr_tache=[]

    if request.user.groups.filter(name='Chef de projet').exists():
        user_is_chefProjet=True
        chefProjet = Employe.objects.filter(email_employe=request.user.email).first()
        if chefProjet:
            projets = Projet.objects.filter(chefProjet=chefProjet)
            nbr_projets=projets.count()
        else:
            projets = None  
        if projets.count() == 1:
            chef_projet_un_projet = True
            form_valid=True
            projet=projets.first()
            avancement = projet.avancement
            avancement_label = dict(Projet.avancement_choices).get(avancement)
            if avancement == '1' or avancement == '7':
                avnc_color="bleu"
            elif avancement=='4' or avancement=='5' or avancement=='6' :
                avnc_color="red"
            elif avancement == '2' or avancement == '3':
                avnc_color="green"
            print(avancement)
            if  avancement == '7':
                print("############################################### avancement7")
                projet_non_finis=True
            
            projet.date_debut = datetime.combine(projet.date_debut, datetime.min.time())
            projet.date_fin = datetime.combine(projet.date_fin, datetime.min.time())
            duree=(projet.date_fin-projet.date_debut).days
            dureeD = (datetime.now() - projet.date_debut).days
            avancement_normal = float("{:.5f}".format(100 / duree))
            if projet.progress == 0:
                projet_pas_commence=True
            
            if dureeD==0:
                progressParJour = float("{:.5f}".format(projet.progress))
            else:
                progressParJour = float("{:.5f}".format(projet.progress / dureeD))
            if projet.progress == 0:
                projet_pas_commence=True
            else:
                
                days_to_add = int(100/progressParJour)
                print("days to add",days_to_add)
                dateF = projet.date_debut + timedelta(days=days_to_add)
                dif_jour = abs((dateF-projet.date_fin).days)
                dateF=dateF.date()
                projet.date_fin = projet.date_fin.date()
            

            taches = Tache.objects.filter(projet=projet)
            if taches.count()==0:
                tache_exist=False
            else:
                tache_exist=True

            count_tache=taches.count()
            ########## tache par type :
            for t in ['1','2']:
                count=taches.filter(type=t).count()
                count_type_tache.append(count)

            ########## tache par duree :

            count1=0
            count2=0
            count3=0

            for t in taches:
                if (t.date_fin - t.date_debut).days<10:
                    count1+=1
                elif (t.date_fin - t.date_debut).days>=10 and (t.date_fin - t.date_debut).days<30:
                    count2+=1
                elif (t.date_fin - t.date_debut).days>30:
                    count3+=1
            count_duree_tache.append(count1)
            count_duree_tache.append(count2)
            count_duree_tache.append(count3)

            
            ########## tache par nbr employe :
            count1=0
            count2=0
            count3=0
            count4=0
            count5=0

            for t in taches:
                if t.employe.all().count()<25:
                    count1+=1
                elif t.employe.all().count()>=25 and t.employe.all().count()<50:
                    count2+=1
                elif t.employe.all().count()>=50 and t.employe.all().count()<75:
                    count3+=1
                elif t.employe.all().count()>=75 and t.employe.all().count()<100:
                    count4+=1
                elif t.employe.all().count()>=100:
                    count5+=1
            count_employe_tache.append(count1)
            count_employe_tache.append(count2)
            count_employe_tache.append(count3)
            count_employe_tache.append(count4)
            count_employe_tache.append(count5)

            ########## tache par progress :
            count1=0
            count2=0
            count3=0
            count4=0

            for t in taches:
                if t.progress<25:
                    count1+=1
                elif t.progress>=25 and t.progress<50:
                    count2+=1
                elif t.progress>=50 and t.progress<75:
                    count3+=1
                elif t.progress>=75 and t.progress<=100:           
                    count4+=1
                
            count_progress_tache.append(count1)
            count_progress_tache.append(count2)
            count_progress_tache.append(count3)
            count_progress_tache.append(count4)

            ########## tache par nbr soustache :
            count1=0
            count2=0
            count3=0

            for t in taches:
                if t.sous_taches.count() == 0:
                    count1+=1
                elif t.sous_taches.count()>=1 and t.sous_taches.count()<5:
                    count2+=1
                elif t.sous_taches.count()>5:
                    count3+=1
                
                
            count_soustache_tache.append(count1)
            count_soustache_tache.append(count2)
            count_soustache_tache.append(count3)

            ########## tache par nbr incidnet :
            count1=0
            count2=0
            count3=0

            for t in taches:
                if t.incidents.count() == 0:
                    count1+=1
                elif t.incidents.count()>=1 and t.incidents.count()<5:
                    count2+=1
                elif t.incidents.count()>5:
                    count3+=1
                
                
            count_incident_tache.append(count1)
            count_incident_tache.append(count2)
            count_incident_tache.append(count3)

            # graphes des employés par poste:
            employes = projet.employe.all()
            if employes.count()==0:
                employe_exist=False
            else:
                employe_exist=True
            for i in ['1','2','3','4','5','6','7','8','9','10','11','12','13']:
                count = employes.filter(poste=i).count()
                count_poste_employe.append(count)
            
            # graphes des employés par etat:
            for i in ['1','2']:
                count = employes.filter(etat_employe=i).count()
                count_etat_employe.append(count)

            # graphes des employés par nbr tache:
            count1=0
            count2=0
            count3=0
            for e in employes:
                if taches.filter(employe=e).count() == 0:
                    count1+=1
                elif taches.filter(employe=e).count()> 0 and taches.filter(employe=e).count() <= 5:
                    count2+=1
                elif taches.filter(employe=e).count() > 5:
                    count3+=1
            count_nbr_tache.append(count1)
            count_nbr_tache.append(count2)
            count_nbr_tache.append(count3)
            
            # graphe de commission par dates
            commissions = Comission.objects.filter(projet=projet)
            if commissions.count()==0:
                comission_exist=False
            else:
                comission_exist=True

            for c in commissions:
                dates_commission.append(c.date)

            dates_commission = set(dates_commission)
            dates_commission = list(dates_commission)
            
            for d in dates_commission:
                count = commissions.filter(date=d).count()
                count_dates_commission.append(count)


            #graphe commission par type
            for t in ['1','2','3']:
                count = commissions.filter(type=t).count()
                count_type_commission.append(count)

            # graphe de document par dates
            documents = Document.objects.filter(projet=projet)
            if documents.count()==0:
                document_exist=False
            else:
                document_exist=True
            for d in documents:
                dates_document.append(d.date)

            dates_document = set(dates_document)
            dates_document = list(dates_document)

            for d in dates_document:
                count = documents.filter(date=d).count()
                count_dates_document.append(count)

            #graphe document par type
            for d in documents:
                type_document.append(d.type)
            type_document = set(type_document)
            type_document = list(type_document)

            for t in type_document:
                count = documents.filter(type=t).count()
                count_type_document.append(count)

            context={
                'form': form,
                'form_valid':form_valid,
                'message':message,
                'chef_projet_un_projet':chef_projet_un_projet,
                'user_is_admin':user_is_admin,
                'user_is_chefProjet':user_is_chefProjet,
                'projet':projet,
                'avancement':avancement_label,
                'avnc_color':avnc_color,
                'progressParJour':progressParJour,
                'dateF':dateF,
                'dif_jour':dif_jour,
                'projet_pas_commence':projet_pas_commence,
                'avancement_normal':avancement_normal,
                'projet_non_finis':projet_non_finis,
                'nbr_projets':nbr_projets,
                'tache_exist':tache_exist,
                'employe_exist':employe_exist,
                'comission_exist':comission_exist,
                'document_exist':document_exist,


                'taches':taches,
                'count_tache':count_tache, 

                'type_tache' :type_tache,
                'count_type_tache':count_type_tache,

                'duree_tache':duree_tache,
                'count_duree_tache':count_duree_tache,

                'type_employe_tache':type_employe_tache,
                'count_employe_tache':count_employe_tache,

                'type_progress_tache':type_progress_tache,
                'count_progress_tache':count_progress_tache,

                'type_soustache_tache':type_soustache_tache,
                'count_soustache_tache':count_soustache_tache,

                'type_incident_tache':type_incident_tache,
                'count_incident_tache':count_incident_tache,

                'poste_employe':poste_employe,
                'count_poste_employe':count_poste_employe,

                'etat_employe':etat_employe,
                'count_etat_employe': count_etat_employe,

                'nbr_tache':nbr_tache,
                'count_nbr_tache': count_nbr_tache,

                'dates_commission':dates_commission,
                'count_dates_commission':count_dates_commission,

                'type_commission':type_commission,
                'count_type_commission':count_type_commission,

                'dates_document':dates_document,
                'count_dates_document':count_dates_document,

                'type_document':type_document,
                'count_type_document':count_type_document,

        }
            return render(request, 'projet_dashboard.html', context)
        
        elif projets.count() > 1:
            if request.method == 'POST':
                if form.is_valid():
                    nom_projet = form.cleaned_data['projet_name']
                    projet = Projet.objects.filter(nom_projet=nom_projet, chefProjet=chefProjet).first()  # Use .first() to get only one object
                    if projet:
                        form_valid = True
                        avancement = projet.avancement
                        avancement_label = dict(Projet.avancement_choices).get(avancement)
                        if avancement == '1' or avancement == '7':
                            avnc_color="bleu"
                        elif avancement=='4' or avancement=='5' or avancement=='6' :
                            avnc_color="red"
                        elif avancement == '2' or avancement == '3':
                            avnc_color="green"
                        print(avancement)
                        
                        if  avancement == '7':
                            print("############################################### avancement7")

                            projet_non_finis=True
                        

                        projet.date_debut = datetime.combine(projet.date_debut, datetime.min.time())
                        projet.date_fin = datetime.combine(projet.date_fin, datetime.min.time())
                        duree=(projet.date_fin-projet.date_debut).days
                        dureeD = (datetime.now() - projet.date_debut).days
                        avancement_normal = float("{:.5f}".format(100 / duree))

                        if projet.progress == 0:
                            projet_pas_commence=True
                        else:
                            if dureeD==0:
                                progressParJour = float("{:.5f}".format(projet.progress ))
                            else:
                                progressParJour = float("{:.5f}".format(projet.progress / dureeD))

                            days_to_add = int(100/progressParJour)
                            dateF = projet.date_debut + timedelta(days=days_to_add)
                            dif_jour = abs((dateF-projet.date_fin).days)
                            dateF=dateF.date()
                            projet.date_fin = projet.date_fin.date()
                        

                        taches = Tache.objects.filter(projet=projet)
                        if taches.count()==0:
                            tache_exist=False
                        else:
                            tache_exist=True
                        count_tache=taches.count()
                        ########## tache par type :
                        for t in ['1','2']:
                            count=taches.filter(type=t).count()
                            count_type_tache.append(count)

                        ########## tache par duree :

                        count1=0
                        count2=0
                        count3=0

                        for t in taches:
                            if (t.date_fin - t.date_debut).days<10:
                                count1+=1
                            elif (t.date_fin - t.date_debut).days>=10 and (t.date_fin - t.date_debut).days<30:
                                count2+=1
                            elif (t.date_fin - t.date_debut).days>30:
                                count3+=1
                        count_duree_tache.append(count1)
                        count_duree_tache.append(count2)
                        count_duree_tache.append(count3)

                        
                        ########## tache par nbr employe :
                        count1=0
                        count2=0
                        count3=0
                        count4=0
                        count5=0

                        for t in taches:
                            if t.employe.all().count()<25:
                                count1+=1
                            elif t.employe.all().count()>=25 and t.employe.all().count()<50:
                                count2+=1
                            elif t.employe.all().count()>=50 and t.employe.all().count()<75:
                                count3+=1
                            elif t.employe.all().count()>=75 and t.employe.all().count()<100:
                                count4+=1
                            elif t.employe.all().count()>=100:
                                count5+=1
                        count_employe_tache.append(count1)
                        count_employe_tache.append(count2)
                        count_employe_tache.append(count3)
                        count_employe_tache.append(count4)
                        count_employe_tache.append(count5)

                        ########## tache par progress :
                        count1=0
                        count2=0
                        count3=0
                        count4=0

                        for t in taches:
                            if t.progress<25:
                                count1+=1
                            elif t.progress>=25 and t.progress<50:
                                count2+=1
                            elif t.progress>=50 and t.progress<75:
                                count3+=1
                            elif t.progress>=75 and t.progress<=100:           
                                count4+=1
                            
                        count_progress_tache.append(count1)
                        count_progress_tache.append(count2)
                        count_progress_tache.append(count3)
                        count_progress_tache.append(count4)

                        ########## tache par nbr soustache :
                        count1=0
                        count2=0
                        count3=0

                        for t in taches:
                            if t.sous_taches.count() == 0:
                                count1+=1
                            elif t.sous_taches.count()>=1 and t.sous_taches.count()<5:
                                count2+=1
                            elif t.sous_taches.count()>5:
                                count3+=1
                            
                            
                        count_soustache_tache.append(count1)
                        count_soustache_tache.append(count2)
                        count_soustache_tache.append(count3)

                        ########## tache par nbr incidnet :
                        count1=0
                        count2=0
                        count3=0

                        for t in taches:
                            if t.incidents.count() == 0:
                                count1+=1
                            elif t.incidents.count()>=1 and t.incidents.count()<5:
                                count2+=1
                            elif t.incidents.count()>5:
                                count3+=1
                            
                            
                        count_incident_tache.append(count1)
                        count_incident_tache.append(count2)
                        count_incident_tache.append(count3)

                        # graphes des employés par poste:
                        employes = projet.employe.all()
                        if employes.count()==0:
                            employe_exist=False
                        else:
                            employe_exist=True
                        for i in ['1','2','3','4','5','6','7','8','9','10','11','12','13']:
                            count = employes.filter(poste=i).count()
                            count_poste_employe.append(count)
                        
                        # graphes des employés par etat:
                        for i in ['1','2']:
                            count = employes.filter(etat_employe=i).count()
                            count_etat_employe.append(count)

                        # graphes des employés par nbr tache:
                        count1=0
                        count2=0
                        count3=0
                        for e in employes:
                            if taches.filter(employe=e).count() == 0:
                                count1+=1
                            elif taches.filter(employe=e).count()> 0 and taches.filter(employe=e).count() <= 5:
                                count2+=1
                            elif taches.filter(employe=e).count() > 5:
                                count3+=1
                        count_nbr_tache.append(count1)
                        count_nbr_tache.append(count2)
                        count_nbr_tache.append(count3)
                        
                        # graphe de commission par dates
                        commissions = Comission.objects.filter(projet=projet)
                        if commissions.count()==0:
                            comission_exist=False
                        else:
                            comission_exist=True
                        for c in commissions:
                            dates_commission.append(c.date)

                        dates_commission = set(dates_commission)
                        dates_commission = list(dates_commission)
                        
                        for d in dates_commission:
                            count = commissions.filter(date=d).count()
                            count_dates_commission.append(count)


                        #graphe commission par type
                        for t in ['1','2']:
                            count = commissions.filter(type=t).count()
                            count_type_commission.append(count)

                        # graphe de document par dates
                        documents = Document.objects.filter(projet=projet)
                        if documents.count()==0:
                            document_exist=False
                        else:
                            document_exist=True
                        for d in documents:
                            dates_document.append(d.date)

                        dates_document = set(dates_document)
                        dates_document = list(dates_document)

                        for d in dates_document:
                            count = documents.filter(date=d).count()
                            count_dates_document.append(count)

                        #graphe document par type
                        for d in documents:
                            type_document.append(d.type)
                        type_document = set(type_document)
                        type_document = list(type_document)

                        for t in type_document:
                            count = documents.filter(type=t).count()
                            count_type_document.append(count)
                        

                    else:
                        similar_projects = process.extract(nom_projet, Projet.objects.filter(chefProjet=chefProjet).values_list('nom_projet', flat=True), limit=5)
                        similar_project_names = [name for name, score in similar_projects if score >= 70]
                        if similar_project_names:
                            message = f"Le projet n'existe pas. Projets similaires : {', '.join(similar_project_names)}"
                        else:
                            message = "Le projet n'existe pas."

        #Pour le graphes de projets par les années :
            current_year = timezone.now().year
            years = list(range(current_year - 4, current_year + 1))

            projet_count_by_year = []
            for year in years:
                count = Projet.objects.filter(date_debut__year=year,chefProjet=chefProjet).count()
                projet_count_by_year.append(count)

        # Pour le graphes de projets par les MO :
            MO = MaitreOuvrage.objects.all()
            projet_count_by_MO = []
            for m in MO:
                count = Projet.objects.filter(maitreOuvrage=m,chefProjet=chefProjet).count()
                projet_count_by_MO.append(count)  # Append to projet_count_by_MO

            # Pour le graphes de projets par les durées :
            durees = [
            'un mois à 6mois',   # Projects with duration less than 6 months
            '6 mois a une année',  # Projects with duration between 6 months and 1 year
            'plus d une anné',    # Projects with duration more than 1 year
            ]

            projet_count_by_duree = []

            
            projects = Projet.objects.filter(chefProjet=chefProjet)
            count1=0
            count2=0
            count3=0
            for p in projects:
                if (p.date_fin-p.date_debut).days >= 30 and (p.date_fin-p.date_debut).days <= (6*30):
                    count1+=1
                elif (p.date_fin-p.date_debut).days > (6*30) and (p.date_fin-p.date_debut).days <= (12*30):
                    count2+=1
                elif (p.date_fin-p.date_debut).days > (12*30):
                    count3+=1

            projet_count_by_duree.append(count1)
            projet_count_by_duree.append(count2)
            projet_count_by_duree.append(count3)

        # Pour le graphes de projets par les etats :

            etats = ['commencé', 'finis']
            projet_count_by_etat = []

            # Count projects with states "commencé" and "finis"
            for etat in etats:
                count = Projet.objects.filter(latest_etat__contains=etat,chefProjet=chefProjet).count()
                projet_count_by_etat.append(count)

            # Count projects with states not in ["commencé", "finis"]
            autre_etat_count = Projet.objects.filter(chefProjet=chefProjet).exclude(latest_etat__in=etats).count()
            projet_count_by_etat.append(autre_etat_count)
            etats = ['commencé', 'finis','autre etat']

        # Pour le graphes de projets par les MO :
            MO = MaitreOuvrage.objects.all()
            projet_count_by_MO = []
            for m in MO:
                count = Projet.objects.filter(maitreOuvrage=m,chefProjet=chefProjet).count()
                projet_count_by_MO.append(count)  # Append to projet_count_by_MO

        # Pour le graphes de projets par l'avancement :
            avancement_choices = [
                'normal',
                'bien',
                'trés bien',
                'mauvaise',
                'trés mauvaise',
                'pas encore commencé',
            ]
            projet_count_by_avancement = []
            i = ['1','2','3','4','5','6']
            for a in i:
                count = Projet.objects.filter(avancement=a,chefProjet=chefProjet).count()
                projet_count_by_avancement.append(count)
            
            

            
            if not form_valid:
                context = {
                    'form': form,
                    'form_valid':form_valid,
                    'message':message,
                    'user_is_admin':user_is_admin,
                'user_is_chefProjet':user_is_chefProjet,
                    'chef_projet_un_projet':chef_projet_un_projet,
                'projet_non_finis':projet_non_finis,
                'nbr_projets':nbr_projets,
                'tache_exist':tache_exist,
                'employe_exist':employe_exist,
                'comission_exist':comission_exist,
                'document_exist':document_exist,


                    'years': years,
                    'projet_count_by_year': projet_count_by_year,

                    'MO':MO,
                    'projet_count_by_MO':projet_count_by_MO,

                    'durees':durees,
                    'projet_count_by_duree':projet_count_by_duree,

                    'etats':etats,
                    'projet_count_by_etat':projet_count_by_etat,

                    'avancement_choices':avancement_choices,
                    'projet_count_by_avancement':projet_count_by_avancement,
                }
            else:
                context = {
                    'form': form,
                    'form_valid':form_valid,
                    'message':message,
                    'user_is_admin':user_is_admin,
                'user_is_chefProjet':user_is_chefProjet,
                    'chef_projet_un_projet':chef_projet_un_projet,
                    'tache_exist':tache_exist,
                'employe_exist':employe_exist,
                'comission_exist':comission_exist,
                'document_exist':document_exist,
                    
                    'projet':projet,
                    'avancement':avancement_label,
                    'avnc_color':avnc_color,
                    'progressParJour':progressParJour,
                    'dateF':dateF,
                    'dif_jour':dif_jour,
                    'projet_pas_commence':projet_pas_commence,
                    'avancement_normal':avancement_normal,
                'projet_non_finis':projet_non_finis,


                    'taches':taches,
                    'count_tache':count_tache, 

                    'type_tache' :type_tache,
                    'count_type_tache':count_type_tache,

                    'duree_tache':duree_tache,
                    'count_duree_tache':count_duree_tache,

                    'type_employe_tache':type_employe_tache,
                    'count_employe_tache':count_employe_tache,

                    'type_progress_tache':type_progress_tache,
                    'count_progress_tache':count_progress_tache,

                    'type_soustache_tache':type_soustache_tache,
                    'count_soustache_tache':count_soustache_tache,

                    'type_incident_tache':type_incident_tache,
                    'count_incident_tache':count_incident_tache,

                    'poste_employe':poste_employe,
                    'count_poste_employe':count_poste_employe,

                    'etat_employe':etat_employe,
                    'count_etat_employe': count_etat_employe,

                    'nbr_tache':nbr_tache,
                    'count_nbr_tache': count_nbr_tache,

                    'dates_commission':dates_commission,
                    'count_dates_commission':count_dates_commission,

                    'type_commission':type_commission,
                    'count_type_commission':count_type_commission,

                    'dates_document':dates_document,
                    'count_dates_document':count_dates_document,

                    'type_document':type_document,
                    'count_type_document':count_type_document,

                }

            
        
        return render(request, 'projet_dashboard.html', context)
    
     
    else:
        user_is_admin=True
        if request.method == 'POST':
            if form.is_valid():
                nom_projet = form.cleaned_data['projet_name']
                projet = Projet.objects.filter(nom_projet=nom_projet).first()  # Use .first() to get only one object
                if projet:
                    form_valid = True
                    avancement = projet.avancement
                    avancement_label = dict(Projet.avancement_choices).get(avancement)
                    if avancement == '1':
                        avnc_color="bleu"
                    elif avancement>='4':
                        avnc_color="red"
                    else:
                        avnc_color="green"
                    if  avancement == '7':
                            print("############################################### avancement7")

                            projet_non_finis=True
                    projet.date_debut = datetime.combine(projet.date_debut, datetime.min.time())
                    projet.date_fin = datetime.combine(projet.date_fin, datetime.min.time())
                    duree=(projet.date_fin-projet.date_debut).days
                    dureeD = (datetime.now() - projet.date_debut).days
                    if dureeD==0:
                        dureeD=1
                    avancement_normal = float("{:.5f}".format(100 / duree))

                    if projet.progress == 0:
                        projet_pas_commence=True
                    else:
                        
                        progressParJour = float("{:.5f}".format(projet.progress / dureeD))
                        days_to_add = int(100/progressParJour)
                        dateF = projet.date_debut + timedelta(days=days_to_add)
                        dif_jour = abs((dateF-projet.date_fin).days)
                        dateF=dateF.date()
                        projet.date_fin = projet.date_fin.date()
                    

                    taches = Tache.objects.filter(projet=projet)
                    if taches.count()==0:
                        tache_exist=False
                    else:
                        tache_exist=True
                    count_tache=taches.count()
                    ########## tache par type :
                    for t in ['1','2']:
                        count=taches.filter(type=t).count()
                        count_type_tache.append(count)

                    ########## tache par duree :

                    count1=0
                    count2=0
                    count3=0

                    for t in taches:
                        if (t.date_fin - t.date_debut).days<10:
                            count1+=1
                        elif (t.date_fin - t.date_debut).days>=10 and (t.date_fin - t.date_debut).days<30:
                            count2+=1
                        elif (t.date_fin - t.date_debut).days>30:
                            count3+=1
                    count_duree_tache.append(count1)
                    count_duree_tache.append(count2)
                    count_duree_tache.append(count3)

                    
                    ########## tache par nbr employe :
                    count1=0
                    count2=0
                    count3=0
                    count4=0
                    count5=0

                    for t in taches:
                        if t.employe.all().count()<25:
                            count1+=1
                        elif t.employe.all().count()>=25 and t.employe.all().count()<50:
                            count2+=1
                        elif t.employe.all().count()>=50 and t.employe.all().count()<75:
                            count3+=1
                        elif t.employe.all().count()>=75 and t.employe.all().count()<100:
                            count4+=1
                        elif t.employe.all().count()>=100:
                            count5+=1
                    count_employe_tache.append(count1)
                    count_employe_tache.append(count2)
                    count_employe_tache.append(count3)
                    count_employe_tache.append(count4)
                    count_employe_tache.append(count5)

                    ########## tache par progress :
                    count1=0
                    count2=0
                    count3=0
                    count4=0

                    for t in taches:
                        if t.progress<25:
                            count1+=1
                        elif t.progress>=25 and t.progress<50:
                            count2+=1
                        elif t.progress>=50 and t.progress<75:
                            count3+=1
                        elif t.progress>=75 and t.progress<=100:           
                            count4+=1
                        
                    count_progress_tache.append(count1)
                    count_progress_tache.append(count2)
                    count_progress_tache.append(count3)
                    count_progress_tache.append(count4)

                    ########## tache par nbr soustache :
                    count1=0
                    count2=0
                    count3=0

                    for t in taches:
                        if t.sous_taches.count() == 0:
                            count1+=1
                        elif t.sous_taches.count()>=1 and t.sous_taches.count()<5:
                            count2+=1
                        elif t.sous_taches.count()>5:
                            count3+=1
                        
                        
                    count_soustache_tache.append(count1)
                    count_soustache_tache.append(count2)
                    count_soustache_tache.append(count3)

                    ########## tache par nbr incidnet :
                    count1=0
                    count2=0
                    count3=0

                    for t in taches:
                        if t.incidents.count() == 0:
                            count1+=1
                        elif t.incidents.count()>=1 and t.incidents.count()<5:
                            count2+=1
                        elif t.incidents.count()>5:
                            count3+=1
                        
                        
                    count_incident_tache.append(count1)
                    count_incident_tache.append(count2)
                    count_incident_tache.append(count3)

                    # graphes des employés par poste:
                    employes = projet.employe.all()
                    if employes.count()==0:
                        employe_exist=False
                    else:
                        employe_exist=True
                    for i in ['1','2','3','4','5','6','7','8','9','10','11','12','13']:
                        count = employes.filter(poste=i).count()
                        count_poste_employe.append(count)
                    
                    # graphes des employés par etat:
                    for i in ['1','2']:
                        count = employes.filter(etat_employe=i).count()
                        count_etat_employe.append(count)

                    # graphes des employés par nbr tache:
                    count1=0
                    count2=0
                    count3=0
                    for e in employes:
                        if taches.filter(employe=e).count() == 0:
                            count1+=1
                        elif taches.filter(employe=e).count()> 0 and taches.filter(employe=e).count() <= 5:
                            count2+=1
                        elif taches.filter(employe=e).count() > 5:
                            count3+=1
                    count_nbr_tache.append(count1)
                    count_nbr_tache.append(count2)
                    count_nbr_tache.append(count3)
                    
                    # graphe de commission par dates
                    commissions = Comission.objects.filter(projet=projet)
                    if commissions.count()==0:
                        comission_exist=False
                    else:
                        comission_exist=True
                    for c in commissions:
                        dates_commission.append(c.date)

                    dates_commission = set(dates_commission)
                    dates_commission = list(dates_commission)
                    
                    for d in dates_commission:
                        count = commissions.filter(date=d).count()
                        count_dates_commission.append(count)


                    #graphe commission par type
                    for t in ['1','2']:
                        count = commissions.filter(type=t).count()
                        count_type_commission.append(count)

                    # graphe de document par dates
                    documents = Document.objects.filter(projet=projet)
                    if documents.count()==0:
                        document_exist=False
                    else:
                        document_exist=True
                    for d in documents:
                        dates_document.append(d.date)

                    dates_document = set(dates_document)
                    dates_document = list(dates_document)

                    for d in dates_document:
                        count = documents.filter(date=d).count()
                        count_dates_document.append(count)

                    #graphe document par type
                    for d in documents:
                        type_document.append(d.type)
                    type_document = set(type_document)
                    type_document = list(type_document)

                    for t in type_document:
                        count = documents.filter(type=t).count()
                        count_type_document.append(count)
                    

                else:
                    similar_projects = process.extract(nom_projet, Projet.objects.values_list('nom_projet', flat=True), limit=5)
                    similar_project_names = [name for name, score in similar_projects if score >= 70]
                    if similar_project_names:
                        message = f"Le projet n'existe pas. Projets similaires : {', '.join(similar_project_names)}"
                    else:
                        message = "Le projet n'existe pas."

        nbr_projets=Projet.objects.all().count()
    #Pour le graphes de projets par les années :
        current_year = timezone.now().year
        years = list(range(current_year - 4, current_year + 1))

        projet_count_by_year = []
        for year in years:
            count = Projet.objects.filter(date_debut__year=year).count()
            projet_count_by_year.append(count)

    # Pour le graphes de projets par les MO :
        MO = MaitreOuvrage.objects.all()
        projet_count_by_MO = []
        for m in MO:
            count = Projet.objects.filter(maitreOuvrage=m).count()
            projet_count_by_MO.append(count)  # Append to projet_count_by_MO

        # Pour le graphes de projets par les durées :
        durees = [
        'un mois à 6mois',   # Projects with duration less than 6 months
        '6 mois a une année',  # Projects with duration between 6 months and 1 year
        'plus d une anné',    # Projects with duration more than 1 year
        ]

        projet_count_by_duree = []

        
        projects = Projet.objects.all()
        count1=0
        count2=0
        count3=0
        for p in projects:
            if (p.date_fin-p.date_debut).days >= 30 and (p.date_fin-p.date_debut).days <= (6*30):
                count1+=1
            elif (p.date_fin-p.date_debut).days > (6*30) and (p.date_fin-p.date_debut).days <= (12*30):
                count2+=1
            elif (p.date_fin-p.date_debut).days > (12*30):
                count3+=1

        projet_count_by_duree.append(count1)
        projet_count_by_duree.append(count2)
        projet_count_by_duree.append(count3)

    # Pour le graphes de projets par les etats :
        etats = ['commencé', 'finis']
        projet_count_by_etat = []

        # Count projects with states "commencé" and "finis"
        for etat in etats:
            count = Projet.objects.filter(latest_etat__contains=etat).count()
            projet_count_by_etat.append(count)

        # Count projects with states not in ["commencé", "finis"]
        autre_etat_count = Projet.objects.exclude(latest_etat__in=etats).count()
        projet_count_by_etat.append(autre_etat_count)
        etats = ['commencé', 'finis','autre etat']

    # Pour le graphes de projets par les MO :
        MO = MaitreOuvrage.objects.all()
        projet_count_by_MO = []
        for m in MO:
            count = Projet.objects.filter(maitreOuvrage=m).count()
            projet_count_by_MO.append(count)  # Append to projet_count_by_MO

    # Pour le graphes de projets par l'avancement :
        avancement_choices = [
            'normal',
            'bien',
            'trés bien',
            'mauvaise',
            'trés mauvaise',
            'pas encore commencé',
        ]
        projet_count_by_avancement = []
        i = ['1','2','3','4','5','6']
        for a in i:
            count = Projet.objects.filter(avancement=a).count()
            projet_count_by_avancement.append(count)
        
        

        
        if not form_valid:
            context = {
                'form': form,
                'form_valid':form_valid,
                'message':message,
                'user_is_admin':user_is_admin,
                'user_is_chefProjet':user_is_chefProjet,
                'chef_projet_un_projet':chef_projet_un_projet,
                'projet_non_finis':projet_non_finis,
                'nbr_projets':nbr_projets,
                'tache_exist':tache_exist,
                'employe_exist':employe_exist,
                'comission_exist':comission_exist,
                'document_exist':document_exist,


                'years': years,
                'projet_count_by_year': projet_count_by_year,

                'MO':MO,
                'projet_count_by_MO':projet_count_by_MO,

                'durees':durees,
                'projet_count_by_duree':projet_count_by_duree,

                'etats':etats,
                'projet_count_by_etat':projet_count_by_etat,

                'avancement_choices':avancement_choices,
                'projet_count_by_avancement':projet_count_by_avancement,
            }
        else:
            context = {
                'form': form,
                'form_valid':form_valid,
                'message':message,
                'user_is_admin':user_is_admin,
                'user_is_chefProjet':user_is_chefProjet,
                'chef_projet_un_projet':chef_projet_un_projet,
                'projet_non_finis':projet_non_finis,
                'nbr_projets':nbr_projets,
                'tache_exist':tache_exist,
                'employe_exist':employe_exist,
                'comission_exist':comission_exist,
                'document_exist':document_exist,

                
                'projet':projet,
                'avancement':avancement_label,
                'avnc_color':avnc_color,
                'progressParJour':progressParJour,
                'dateF':dateF,
                'dif_jour':dif_jour,
                'projet_pas_commence':projet_pas_commence,
                'avancement_normal':avancement_normal,

                'taches':taches,
                'count_tache':count_tache, 

                'type_tache' :type_tache,
                'count_type_tache':count_type_tache,

                'duree_tache':duree_tache,
                'count_duree_tache':count_duree_tache,

                'type_employe_tache':type_employe_tache,
                'count_employe_tache':count_employe_tache,

                'type_progress_tache':type_progress_tache,
                'count_progress_tache':count_progress_tache,

                'type_soustache_tache':type_soustache_tache,
                'count_soustache_tache':count_soustache_tache,

                'type_incident_tache':type_incident_tache,
                'count_incident_tache':count_incident_tache,

                'poste_employe':poste_employe,
                'count_poste_employe':count_poste_employe,

                'etat_employe':etat_employe,
                'count_etat_employe': count_etat_employe,

                'nbr_tache':nbr_tache,
                'count_nbr_tache': count_nbr_tache,

                'dates_commission':dates_commission,
                'count_dates_commission':count_dates_commission,

                'type_commission':type_commission,
                'count_type_commission':count_type_commission,

                'dates_document':dates_document,
                'count_dates_document':count_dates_document,

                'type_document':type_document,
                'count_type_document':count_type_document,

            }

        
    
    return render(request, 'projet_dashboard.html', context)

from django.shortcuts import render, redirect

def tache_dashboard(request):
    form_projet = ProjetNameForm2(request.POST or None)
    user_is_chefProjet = False
    user_is_admin = False
    chef_projet_un_projet = False
    message = None

    if request.user.groups.filter(name='Chef de projet').exists():
        chefProjet = Employe.objects.filter(email_employe=request.user.email).first()
        if chefProjet:
            projets = Projet.objects.filter(chefProjet=chefProjet)
        else:
            projets = None  
        if projets.count() == 1:
            chef_projet_un_projet = True
            projet = Projet.objects.filter(chefProjet=chefProjet).first()
        user_is_chefProjet = True
    else:
        user_is_admin = True 

    if user_is_chefProjet and chef_projet_un_projet:
        return redirect('tache_dashboardd')  # Redirect to tache_dashboardd view
    else:
        if request.method == 'POST':
            if form_projet.is_valid():
                nom_projet = form_projet.cleaned_data['projet_name']
                projet = Projet.objects.filter(nom_projet=nom_projet).first()
                if not projet:
                    similar_projects = process.extract(nom_projet, Projet.objects.values_list('nom_projet', flat=True), limit=5)
                    similar_project_names = [name for name, score in similar_projects if score >= 70]
                    if similar_project_names:
                        message = f"Le projet n'existe pas. Projets similaires : {', '.join(similar_project_names)}"
                    else:
                        message = "Le projet n'existe pas."
                elif projet and user_is_chefProjet:
                    if not Projet.objects.filter(nom_projet=nom_projet, chefProjet=chefProjet).exists():
                        similar_projects = process.extract(nom_projet, Projet.objects.filter(chefProjet=chefProjet).values_list('nom_projet', flat=True), limit=5)
                        similar_project_names = [name for name, score in similar_projects if score >= 70]
                        if similar_project_names:
                            message = f"Le projet n'existe pas. Projets similaires : {', '.join(similar_project_names)}"
                            return render(request, 'tache_dashboard.html', {'form_projet': form_projet,'message': message,'user_is_admin':user_is_admin,'user_is_chefProjet':user_is_chefProjet})
                        else:
                            message = "Le projet n'existe pas."
                            return render(request, 'tache_dashboard.html', {'form_projet': form_projet,'message': message,'user_is_admin':user_is_admin,'user_is_chefProjet':user_is_chefProjet})
                    else:
                        return redirect('tache_dashboardd_with_id', projet_id=projet.id_projet)  # Redirect to tache_dashboardd view
                else:
                    return redirect('tache_dashboardd_with_id', projet_id=projet.id_projet)  # Redirect to tache_dashboardd view

    return render(request, 'tache_dashboard.html', {'form_projet': form_projet, 'message': message,'user_is_admin':user_is_admin,'user_is_chefProjet':user_is_chefProjet})  
                    

from collections import defaultdict

def build_project_structure(projet):
  

  project_data = {
      "name": projet.nom_projet,
      "progress": projet.progress,  # Keep original progress
      "duree": (projet.date_fin - projet.date_debut).days,
  }

  # Create a dictionary to efficiently map tasks to their parent tasks
  task_parent_map = defaultdict(list)
  for tache in projet.taches.all():
    task_parent_map[tache.tache_mere.id_tache if tache.tache_mere else None].append(tache)

  def build_task_structure(task):
   
    task_data = {
        "name": task.nom_tache,
        "progress": float("{:.3f}".format(task.progress)),  # Keep original task progress
        "duree": (task.date_fin - task.date_debut).days,
        "avancement": task.avancement,  # Keep original advancement
    }

    children = task_parent_map.get(task.id_tache, [])
    if children:
      task_data["children"] = []
      for child_task in children:
        child_data = build_task_structure(child_task)
        task_data["children"].append(child_data)

    return task_data

  # Call the recursive function to build the task structure for the main project
  project_data["children"] = [build_task_structure(task) for task in task_parent_map[None]]

  return project_data






def tache_dashboardd(request, projet_id=None):
    form_tache = TacheNameForm(request.POST or None)
    user_is_chefProjet = False
    user_is_admin = False
    chef_projet_un_projet = False
    tache=None
    message = None
    msggg = None
    taches_general=True
    avancement_label=None
    avancement_normal=None
    avnc_color=None
    tache_non_finis=True
    tache_pas_commence=False
    progressParJour=None
    dateF=None
    dif_jour=None
    wbs_data=None
    emplpoye_exist=True
    ressource_exist=True

    poste_employe = ['President Directeur Générale', 'Directeur Générale','Assistant','Consultant', 'Chef Stucture','Ingénieur d informatique', 'Ingénieur D Etudes','Chargé D Etudes ', 'Exploitant ', 'Ingénieur de Génie Civile ','Chef Projet', 'Chef Tache','Autre']
    count_poste_employe=[]

    etat_employe = ['Célibataire','Mariée']
    count_etat_employe = []

    duree_ressource=['moins de 2 semaines','2 semaines à 1 mois','plus d un mois']
    count_duree_ressource=[]

    etat_ressource=['Bonne Etat','Endomagé','En Panne']
    count_etat_ressource=[]

    type_ressource=['Matériel de Transport','Matériel pour le Diagnostic','Matériel pour le Mesure','Matériel de Nettoyage','Matériel pour gros oeuvre','Matériel pour second oeuvre','Matériel pour Espace verts','Matériel pour Industrie','Matériel de Manutention','Matériel de Signalisation','Matériel portatif','Engins de Terrasement','Machines à Projete','Electricité sur chantiers','Autre']
    count_type_ressource=[]




    if request.user.groups.filter(name='Chef de projet').exists():
        chefProjet = Employe.objects.filter(email_employe=request.user.email).first()
        if chefProjet:
            projets = Projet.objects.filter(chefProjet=chefProjet)
        else:
            projets = None  
        if projets.count() == 1:
            chef_projet_un_projet = True
            projet = Projet.objects.filter(chefProjet=chefProjet).first()

        user_is_chefProjet = True
    else:
        user_is_admin = True
        
    if user_is_admin or (user_is_chefProjet and not chef_projet_un_projet):
        projet = get_object_or_404(Projet, pk=projet_id)
    else:
       projet= Projet.objects.filter(chefProjet=chefProjet).first()
    
    if request.method == 'POST':
            if form_tache.is_valid():
                nom_tache = form_tache.cleaned_data['nom_tache']
                tache = Tache.objects.filter(nom_tache=nom_tache,projet=projet).first()
                if not tache:
                    similar_taches = process.extract(nom_tache, Tache.objects.values_list('nom_tache', flat=True), limit=5)
                    similar_taches_names = [name for name, score in similar_taches if score >= 70]
                    if similar_taches_names:
                        message = f"La tache n'existe pas. Taches similaires : {', '.join(similar_taches_names)}"
                    else:
                        message = "La tache n'existe pas."
                else:
                    taches_general=False
                    avancement = tache.avancement
                    print(tache,tache.avancement,avancement)
                    avancement_label = dict(Tache.avancement_choices).get(avancement)
                    if avancement == '1' or avancement == '7':
                        avnc_color="blue"
                    elif avancement=='4' or avancement=='5' or avancement=='6' :
                        avnc_color="red"
                    elif avancement == '2' or avancement == '3':
                        avnc_color="green"
                        
                    if  avancement == '7':
                        tache_non_finis=False
                    tache.date_debut = datetime.combine(tache.date_debut, datetime.min.time())
                    tache.date_fin = datetime.combine(tache.date_fin, datetime.min.time())
                    duree=(tache.date_fin-tache.date_debut).days
                    dureeD = (datetime.now() - tache.date_debut).days
                    if dureeD==0:
                        dureeD=1
                    avancement_normal = float("{:.5f}".format(100 / duree))

                    if tache.progress == 0:
                        tache_pas_commence=True
                    else:
                        
                        progressParJour = float("{:.5f}".format(tache.progress / dureeD))
                        days_to_add = int(100/progressParJour)
                        print("days to add",days_to_add)
                        dateF = tache.date_debut + timedelta(days=days_to_add)
                        dif_jour = abs((dateF-tache.date_fin).days)
                        dateF=dateF.date()
                        tache.date_fin = tache.date_fin.date()

                    # graphes des employés par poste:
                        employes = tache.employe.all()

                        if employes is None:
                            emplpoye_exist=False
                        else:
                            emplpoye_exist=True

                        
                        for i in ['1','2','3','4','5','6','7','8','9','10','11','12','13']:
                            count = employes.filter(poste=i).count()
                            count_poste_employe.append(count)
                        
                    # graphes des employés par etat:
                        for i in ['1','2']:
                            count = employes.filter(etat_employe=i).count()
                            count_etat_employe.append(count)

                    # graphes des ressources par duree
                    count1=0
                    count2=0
                    count3=0
                    utilisation_ressource = UtilisationRessource.objects.filter(tache=tache)
                    if utilisation_ressource.count() == 0:
                            ressource_exist=False
                    else:
                            ressource_exist=True
                    for u in utilisation_ressource:
                        if (u.date_fin-u.date_debut).days<14:
                            count1+=1
                        elif (u.date_fin-u.date_debut).days>=14 and (u.date_fin-u.date_debut).days<30 :
                            count2+=1
                        if (u.date_fin-u.date_debut).days>30:
                            count3+=1
                    count_duree_ressource.append(count1)
                    count_duree_ressource.append(count2)
                    count_duree_ressource.append(count3)

                    # graphes des ressources par etat
                    resources = []
                    for tache_ressource in utilisation_ressource:
                        resources.append(tache_ressource.ressource)

                    for i in ['1','2','3']:
                        count = sum(1 for res in resources if res.etat == i)
                        count_etat_ressource.append(count)
                    
                    #graphes ressource par type
                    for i in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15']:
                        count = sum(1 for res in resources if res.type == i)
                        count_type_ressource.append(count)



    
    msggg = f"{projet.nom_projet}"
    print(emplpoye_exist)
# Usage example:
# Assuming 'projet' is an instance of the Projet model
    wbs_data = build_project_structure(projet)

    context = {
        'form_tache': form_tache,
        'user_is_admin': user_is_admin,
        'user_is_chefProjet': user_is_chefProjet,
        'chef_projet_un_projet': chef_projet_un_projet,
        'message': message,
        'msggg': msggg,
        'wbs_data':wbs_data,
        'tache':tache,
        'taches_general':taches_general,
        'tache_non_finis':tache_non_finis,
        'avancement':avancement_label,
        'avnc_color':avnc_color,
        'progressParJour':progressParJour,
        'dateF':dateF,
        'dif_jour':dif_jour,
        'tache_pas_commence':tache_pas_commence,
        'avancement_normal':avancement_normal,
        'emplpoye_exist':emplpoye_exist,
        'ressource_exist':ressource_exist,

        'poste_employe':poste_employe,
        'count_poste_employe':count_poste_employe,

        'etat_employe':etat_employe,
        'count_etat_employe': count_etat_employe,

        'duree_ressource':duree_ressource,
        'count_duree_ressource':count_duree_ressource,

        'etat_ressource':etat_ressource,
        'count_etat_ressource':count_etat_ressource,

        'type_ressource':type_ressource,
        'count_type_ressource':count_type_ressource,

    }
    return render(request, 'tache_dashboardd.html', context)

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Ressource, UtilisationRessource
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Ressource, UtilisationRessource
from datetime import datetime

@require_http_methods(["GET"])
def get_ressource_details(request, ressource_id):
    try:
        ressource = get_object_or_404(Ressource, pk=ressource_id)
        id = request.GET.get('id_TR')
        date_debut_str = request.GET.get('date_debut')
        date_fin_str = request.GET.get('date_fin')

        if date_debut_str and date_fin_str:
            date_debut = datetime.strptime(date_debut_str, '%d/%m/%Y')
            date_fin = datetime.strptime(date_fin_str, '%d/%m/%Y')
            
            if id:
                utilisation = get_object_or_404(UtilisationRessource, pk=id)
                overlapping_utilisations = UtilisationRessource.objects.filter(
                    Q(ressource=ressource) &
                    (
                        (Q(date_debut__lte=date_fin) & Q(date_fin__gte=date_debut))
                    )
                ).exclude(pk=id)
            else:
                overlapping_utilisations = UtilisationRessource.objects.filter(
                    Q(ressource=ressource) &
                    (
                        (Q(date_debut__lte=date_fin) & Q(date_fin__gte=date_debut))
                    )
                )

            if overlapping_utilisations.exists():
                if id :
                    overlap_dates = [{'date_debut': overlap.date_debut, 'date_fin': overlap.date_fin} for overlap in UtilisationRessource.objects.filter(ressource=ressource).exclude(pk=id)]
                else:

                    overlap_dates = [{'date_debut': overlap.date_debut, 'date_fin': overlap.date_fin} for overlap in UtilisationRessource.objects.filter(ressource=ressource)]
                return JsonResponse({'overlap': True, 'message': 'Les dates sélectionnées se chevauchent avec une autre utilisation de la ressource.', 'overlap_dates': overlap_dates})

        # Collect all utilisation dates for the resource
        all_utilisation_dates = [{'date_debut': utilisation.date_debut, 'date_fin': utilisation.date_fin} for utilisation in UtilisationRessource.objects.filter(ressource=ressource)]

        return JsonResponse({'disponibilite': ressource.disponibilite, 'all_utilisation_dates': all_utilisation_dates})
    except Ressource.DoesNotExist:
        return JsonResponse({'error': 'Ressource not found'}, status=404)
