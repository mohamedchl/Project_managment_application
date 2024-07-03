from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.transaction import on_commit
from .models import Notification, NotificationSeen, User,Incident,IncidentSeen,Projet,Employe,Group,EtatTache,Tache,EtatProjet
from django.db.models.signals import pre_save
from django.dispatch import receiver
from datetime import datetime


"""def create_notification_seen_on_commit(notification):
    
    Inner function to create NotificationSeen objects after commit.

    Args:
        notification (Notification): The saved notification instance.
    
    if not notification:  # Check if notification is None
        return  # Exit the function if notification is None

    employes = notification.employe.all()
    employes_count = employes.count()
    print(f"Number of related employes: {employes_count}")
    admin = User.objects.get(username='admin')
    NotificationSeen.objects.create(user=admin, notification=notification, seen=False)

    for employe in employes:
        user = User.objects.filter(email=employe.email_employe).first()
        if user:
            NotificationSeen.objects.create(user=user, notification=notification, seen=False)
            employe.notificationNotSeen += 1
            employe.save()
        else:
            print(f"Employee '{employe.nom_employe}' does not have an associated User object.")

@receiver(post_save, sender=Notification)
def create_notification_seen_on_notification_save(sender, instance, created, **kwargs):
    
    Creates NotificationSeen objects for all employes with matching emails
    when a new Notification is created.

    Args:
        sender (models.Model): The sender of the signal (Notification in this case).
        instance (Notification): The newly created Notification object.
        created (bool): Whether the object was created (True) or updated (False).
        **kwargs: Additional keyword arguments passed to the signal handler.
    

    if created:
        print(f"Notification instance: {instance}")
        print("Checking related employes...")
        
        # Apply the on_commit decorator to the function
        on_commit(lambda: create_notification_seen_on_commit(instance))

"""
###################################################################################
"""
def create_incident_seen_on_commit(incident):
    
    Inner function to create NotificationSeen objects after commit.

    Args:
        notification (Notification): The saved notification instance.
    
    if not incident:  # Check if notification is None
        return  # Exit the function if notification is None

    employes = incident.employe.all()
    employes_count = employes.count()
    print(f"Number of related employes: {employes_count}")
    admin = User.objects.get(username='admin')
    IncidentSeen.objects.create(user=admin, incident=incident, seen=False)

    for employe in employes:
        user = User.objects.filter(email=employe.email_employe).first()
        if user:
            IncidentSeen.objects.create(user=user, incident=incident, seen=False)
            employe.incidentNotSeen +=1
            employe.save()

        else:
            print(f"Employee '{employe.nom_employe}' does not have an associated User object.")

@receiver(post_save, sender=Incident)
def create_incident_seen_on_incident_save(sender, instance, created, **kwargs):
    
    Creates NotificationSeen objects for all employes with matching emails
    when a new Notification is created.

    Args:
        sender (models.Model): The sender of the signal (Notification in this case).
        instance (Notification): The newly created Notification object.
        created (bool): Whether the object was created (True) or updated (False).
        **kwargs: Additional keyword arguments passed to the signal handler.
    

    if created:
        on_commit(lambda: create_incident_seen_on_commit(instance))

@receiver(pre_save, sender=Incident)
def update_incident_seen_on_employe_change(sender, instance, **kwargs):
    try:
        old_instance = Incident.objects.get(pk=instance.pk)
    except Incident.DoesNotExist:
        # If it's a new instance, there's no old employe to consider
        return

    old_employes = set(old_instance.employe.all())
    new_employes = set(instance.employe.all())

    # Employes to be added
    employes_to_add = new_employes - old_employes
    for employe in employes_to_add:
        user = User.objects.filter(email=employe.email_employe).first()
        if user:
            IncidentSeen.objects.create(user=user, incident=instance, seen=False)
            employe.incidentNotSeen += 1
            employe.save()

    # Employes to be removed
    employes_to_remove = old_employes - new_employes
    for employe in employes_to_remove:
        user = User.objects.filter(email=employe.email_employe).first()
        if user:
            IncidentSeen.objects.filter(user=user, incident=instance).delete()
            employe.incidentNotSeen -= 1
            employe.save()


"""
#####################################################################################




@receiver(post_save, sender=Projet)
def add_chef_de_projet_to_group(sender, instance, created, **kwargs):
    if created: 
        chef_projet_email = instance.chefProjet.email_employe
        chef_de_projet_group, _ = Group.objects.get_or_create(name='Chef de projet')
        user = User.objects.filter(email=chef_projet_email).first()
        if user:
            user.groups.add(chef_de_projet_group)

@receiver(pre_save, sender=Projet)
def update_chef_de_projet_permissions(sender, instance, **kwargs):
    try:
        old_instance = Projet.objects.get(pk=instance.pk)
    except Projet.DoesNotExist:
        # If it's a new instance, there's no old chefProjet to consider
        return

    old_chef_projet = old_instance.chefProjet
    new_chef_projet = instance.chefProjet
    print(old_chef_projet,new_chef_projet)
    if old_chef_projet != new_chef_projet:
        # Remove group permissions from the old chefProjet if they have no other projects
        if old_chef_projet and not Projet.objects.filter(chefProjet=old_chef_projet).exclude(pk=instance.pk).exists():
            chef_de_projet_group = Group.objects.get(name='Chef de projet')
            user = User.objects.filter(email=old_chef_projet.email_employe).first()
            if user:
                user.groups.remove(chef_de_projet_group)

        # Add group permissions to the new chefProjet
        if new_chef_projet:
            chef_de_projet_group = Group.objects.get_or_create(name='Chef de projet')[0]
            user = User.objects.filter(email=new_chef_projet.email_employe).first()
            if user:
                user.groups.add(chef_de_projet_group)




from django.db.models.signals import post_delete
from django.dispatch import receiver





@receiver(post_delete, sender=EtatTache)
def update_progress_on_delete(sender, instance, **kwargs):
    # Decrement the progress when a CheckTache object is deleted
    if instance.tache_finis:
        total_employees = instance.tache.employe.all().count()
        if total_employees > 0:
            progress_decrement = 100 / total_employees
            instance.tache.progress -= progress_decrement
            instance.tache.save()


@receiver(pre_save, sender=EtatTache)
def update_progress_on_tache_finis_change(sender, instance, **kwargs):
    if instance.pk:
        # Fetch the original instance from the database
        original_instance = sender.objects.get(pk=instance.pk)
        
        if original_instance.tache_finis and not instance.tache_finis:
            # If tache_finis is being changed from True to False
            total_employees = instance.tache.employe.all().count()
            if total_employees > 0:
                progress_decrement = 100 / total_employees
                instance.tache.progress -= progress_decrement
                instance.tache.save()
                






from django.db.models.signals import pre_delete



@receiver(pre_delete, sender=Incident)
def incident_pre_delete(sender, instance, **kwargs):
    instance.progress=0
    instance.save()
    instance.update_progress

@receiver(pre_delete, sender=Tache)
def incident_pre_delete(sender, instance, **kwargs):
    instance.progress=0
    instance.save()
    instance.update_progress

@receiver(post_save, sender=Tache)
def tache_post_save(sender, instance, created, **kwargs):
    instance.update_progress
    
        
@receiver(post_save, sender=Incident)
def update_progress_on_incident_save(sender, instance, **kwargs):
    instance.update_progress

@receiver(post_delete, sender=EtatProjet)
def update_etat_on_etatprojet_delete(sender, instance, **kwargs):
    projet = instance.projet
    # Get the latest EtatProjet instance for the projet, if it exists
    latest_etat_instance = EtatProjet.objects.filter(projet=projet).last()
    if latest_etat_instance:
        projet.latest_etat = f"{latest_etat_instance.lib_etat} (le {latest_etat_instance.date_etat.strftime('%Y-%m-%d')})"
    else:
        # If there are no more EtatProjet instances, clear the latest_etat field
        projet.latest_etat = None
    projet.save(update_fields=['latest_etat'])

@receiver(post_save, sender=Projet)
def check_date_fin_create_etat(sender, instance, **kwargs):
    # Get the current date
    current_date = datetime.now()

    # Check if date_fin is updated to a date before the current date
    if instance.pk is not None:
        # Fetch the existing project instance from the database
        existing_projet = Projet.objects.get(pk=instance.pk)
        if existing_projet.date_fin != instance.date_fin and instance.date_fin < current_date:
            # Check if the 'finis' state already exists
            if not EtatProjet.objects.filter(projet=instance, lib_etat='finis').exists():
                EtatProjet.objects.create(lib_etat='finis', date_etat=current_date, projet=instance)

        
@receiver(post_save, sender=Projet)
def create_etat_projet(sender, instance, created, **kwargs):
    if created:
        EtatProjet.objects.create(lib_etat="commencé", date_etat=datetime.now(), projet=instance)

@receiver(post_save, sender=EtatProjet)
def create_etat_projet(sender, instance, created, **kwargs):
    if created:
        projet = instance.projet
        projet.latest_etat = f"{instance.lib_etat} (le {instance.date_etat.strftime('%Y-%m-%d')})"
        projet.save(update_fields=['latest_etat'])
from django.db.models.signals import post_save, m2m_changed, pre_save
from django.dispatch import receiver
from .models import Projet, Notification, Employe, User, NotificationSeen, IncidentSeen, Tache, Incident

@receiver(post_save, sender=Notification)
def create_notification(sender, instance, created, **kwargs):
    if created:
        if instance.employe.exists():
            for employe in instance.employe.all():
                user = User.objects.filter(email=employe.email_employe).first()
                if not NotificationSeen.objects.filter(user=user, notification=instance).exists():
                    NotificationSeen.objects.create(user=user, notification=instance, seen=False)
                    employe.notificationNotSeen += 1
                    employe.save()
        else:
            print("none")

@receiver(post_save, sender=Employe)
def create_user(sender, instance, created, **kwargs):
    if created:
        employe = instance
        username = f"{employe.nom_employe.split()[0]}{employe.matricule}"
        existing_user = User.objects.filter(username=username).first()
        if not existing_user:
            User.objects.create_user(username=username, email=instance.email_employe)
        else:
            existing_user.email = instance.email_employe
            existing_user.save()

@receiver(post_delete, sender=Employe)
def delete_user(sender, instance, **kwargs):
    email = instance.email_employe
    user = User.objects.filter(email=email).first()
    if user:
        user.delete()
        
@receiver(post_save, sender=Tache)
def create_tache_notification(sender, instance, created, **kwargs):
    if created:
        notification = Notification.objects.create(
            type='2',
            titre=f"Affectation a tache '{instance.nom_tache}' de projet '{instance.projet.nom_projet}'",
            details=f'Cher employés, Nous tenons à vous informer que vous avez été affectés à une nouvelle tâche "{instance.nom_tache}" dans le cadre du projet "{instance.projet.nom_projet}". Les détails seront communiqués prochainement.'
        )
        for employe in instance.employe.all():
            user = User.objects.filter(email=employe.email_employe).first()
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                notification.employe.add(employe)
                employe.notificationNotSeen += 1
                employe.save()
        notification.save()

@receiver(m2m_changed, sender=Tache.employe.through)
def update_tache_notification_employees(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        notification_title = f"Affectation a tache '{instance.nom_tache}' de projet '{instance.projet.nom_projet}'"
        notification, created = Notification.objects.get_or_create(
            titre=notification_title,
            defaults={
                'type': '2',
                'details': f'Cher employés, Nous tenons à vous informer que vous avez été affectés à une nouvelle tâche "{instance.nom_tache}" dans le cadre du projet "{instance.projet.nom_projet}". Les détails seront communiqués prochainement.'
            }
        )
        for employe_id in pk_set:
            employe = Employe.objects.get(id_employe=employe_id)
            user = User.objects.filter(email=employe.email_employe).first()
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                notification.employe.add(employe)
                employe.notificationNotSeen += 1
                employe.save()
        notification.save()

@receiver(post_save, sender=Projet)
def create_projet_notification(sender, instance, created, **kwargs):
    if created:
        notification = Notification.objects.create(
            type='2',
            titre=f'Affectation a projet "{instance.nom_projet}"',
            details=f'Cher employés, Nous avons le plaisir de vous informer que vous avez été affecté(e) au projet {instance.nom_projet} qui est géré par le chef "{instance.chefProjet.nom_employe}". Votre expertise et votre contribution seront précieuses pour atteindre nos objectifs communs. Nous sommes impatients de travailler avec vous sur ce projet passionnant.'
        )
        for employe in instance.employe.all():
            user = User.objects.filter(email=employe.email_employe).first()
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                notification.employe.add(employe)
                employe.notificationNotSeen += 1
                employe.save()
        notification.save()

        # Create a separate notification for the chef de projet
        chef_projet = instance.chefProjet
        if chef_projet:
            chef_user = User.objects.filter(email=chef_projet.email_employe).first()
            chef_notification = Notification.objects.create(
                type='2',
                titre=f'Nomination en tant que chef de projet "{instance.nom_projet}"',
                details=f'Félicitations {chef_projet.nom_employe}, vous avez été désigné(e) comme chef de projet pour "{instance.nom_projet}". Nous comptons sur vous pour diriger ce projet avec succès.'
            )
            if chef_user and not NotificationSeen.objects.filter(user=chef_user, notification=chef_notification).exists():
                NotificationSeen.objects.create(user=chef_user, notification=chef_notification, seen=False)
                chef_notification.employe.add(chef_projet)
                chef_projet.notificationNotSeen += 1
                chef_projet.save()
            chef_notification.save()

@receiver(m2m_changed, sender=Projet.employe.through)
def update_projet_notification_employees(sender, instance, action, **kwargs):
    if action == "post_add":
        notification_title = f'Affectation a projet "{instance.nom_projet}"'
        notification = Notification.objects.filter(titre=notification_title).first()
        if notification:
            for employe in instance.employe.all():
                if not notification.employe.filter(pk=employe.pk).exists():
                    user = User.objects.filter(email=employe.email_employe).first()
                    if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                        NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                        notification.employe.add(employe)
                        employe.notificationNotSeen += 1
                        employe.save()
            notification.save()
        else:
            notification = Notification.objects.create(
                type='2',
                titre=f'Affectation a projet "{instance.nom_projet}"',
                details=f'Cher employés, Nous avons le plaisir de vous informer que vous avez été affecté(e) au projet {instance.nom_projet} qui est géré par le chef "{instance.chefProjet.nom_employe}". Votre expertise et votre contribution seront précieuses pour atteindre nos objectifs communs. Nous sommes impatients de travailler avec vous sur ce projet passionnant.'
            )
            for employe in instance.employe.all():
                user = User.objects.filter(email=employe.email_employe).first()
                if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                    NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                    notification.employe.add(employe)
                    employe.notificationNotSeen += 1
                    employe.save()
            notification.save()

@receiver(post_save, sender=Incident)
def create_incident_notification(sender, instance, created, **kwargs):
    if created:
        notification = Notification.objects.create(
            type='3',
            titre=f"Affectation a l'incident '{instance.nom_incident}' de projet '{instance.projet.nom_projet}'",
            details=f'Cher employés, Nous tenons à vous informer que vous avez été affectés à un nouvel incident "{instance.nom_incident}" dans le cadre du projet "{instance.projet.nom_projet}". Les détails seront communiqués prochainement.'
        )
        for employe in instance.employe.all():
            user = User.objects.filter(email=employe.email_employe).first()
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                IncidentSeen.objects.create(user=user, incident=instance, seen=False)
                notification.employe.add(employe)
                employe.incidentNotSeen += 1
                employe.notificationNotSeen += 1
                employe.save()
        notification.save()

@receiver(m2m_changed, sender=Incident.employe.through)
def update_incident_notification_employees(sender, instance, action, pk_set, **kwargs):
    if action == "post_add":
        notification_title = f"Affectation a l'incident '{instance.nom_incident}' de projet '{instance.projet.nom_projet}'"
        notification, created = Notification.objects.get_or_create(
            titre=notification_title,
            defaults={
                'type': '3',
                'details': f'Cher employés, Nous tenons à vous informer que vous avez été affectés à un nouvel incident "{instance.nom_incident}" dans le cadre du projet "{instance.projet.nom_projet}". Les détails seront communiqués prochainement.'
            }
        )
        for employe_id in pk_set:
            employe = Employe.objects.get(id_employe=employe_id)
            user = User.objects.filter(email=employe.email_employe).first()
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                IncidentSeen.objects.create(user=user, incident=instance, seen=False)
                notification.employe.add(employe)
                employe.incidentNotSeen += 1
                employe.notificationNotSeen += 1
                employe.save()
        notification.save()

@receiver(m2m_changed, sender=Notification.employe.through)
def create_notification_status(sender, instance, action, reverse, pk_set, **kwargs):
    if action == 'post_add' and not reverse:
        for employe_id in pk_set:
            employe = Employe.objects.get(pk=employe_id)
            user = User.objects.filter(email=employe.email_employe).first()
            if not NotificationSeen.objects.filter(user=user, notification=instance).exists():
                NotificationSeen.objects.create(user=user, notification=instance, seen=False)
                employe.notificationNotSeen += 1
                employe.save()

@receiver(m2m_changed, sender=Incident.employe.through)
def create_incident_status(sender, instance, action, reverse, pk_set, **kwargs):
    if action == 'post_add' and not reverse:
        for employe_id in pk_set:
            employe = Employe.objects.get(pk=employe_id)
            user = User.objects.filter(email=employe.email_employe).first()
            if not IncidentSeen.objects.filter(user=user, incident=instance).exists():
                IncidentSeen.objects.create(user=user, incident=instance, seen=False)
                employe.incidentNotSeen += 1
                employe.save()

@receiver(pre_save, sender=Projet)
def notify_new_chef_projet(sender, instance, **kwargs):
    if instance.pk:
        previous_instance = Projet.objects.get(pk=instance.pk)
        if instance.chefProjet != previous_instance.chefProjet:
            new_chef = instance.chefProjet
            user = User.objects.filter(email=new_chef.email_employe).first()
            notification = Notification.objects.create(
                type='2',
                titre=f"Nomination en tant que chef de projet '{instance.nom_projet}'",
                details=f'Cher(e) {new_chef.nom_employe}, Nous avons le plaisir de vous informer que vous avez été nommé(e) chef de projet pour "{instance.nom_projet}". Votre leadership et expertise sont très appréciés.'
            )
            if user and not NotificationSeen.objects.filter(user=user, notification=notification).exists():
                NotificationSeen.objects.create(user=user, notification=notification, seen=False)
                notification.employe.add(new_chef)
                new_chef.notificationNotSeen += 1
                new_chef.save()
            notification.save()
