from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import Employe,Projet,EtatProjet,SuiviTache,Tache
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

class EmployeRegistrationForm(forms.Form):
    matricule = forms.IntegerField(
        widget=forms.TextInput(attrs={'placeholder': 'Matricule'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Mot de passe'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmer Mot de passe'})
    )

    def __init__(self, *args, **kwargs):
        super(EmployeRegistrationForm, self).__init__(*args, **kwargs)
        
        # Remove labels for fields
        for field_name, field in self.fields.items():
            field.label = ''

    def clean_matricule(self):
        matricule = self.cleaned_data['matricule']

        existing_employe = Employe.objects.filter(matricule=matricule).first()

        if existing_employe:
            existing_user = User.objects.filter(email=existing_employe.email_employe,is_staff=True).first()

            if existing_user:
                raise forms.ValidationError("Vous avez déja choisi votre mot de passe!.")
        else:
            raise forms.ValidationError("Il n'y a pas un employé de cette matricule.")

        return matricule

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe sont pas le meme.")
        
        if len(password2) < 8:
            raise forms.ValidationError("Le mot de passe doit étre de 8 charachtères a plus.")
        
        return password2


    def save(self, commit=True):
        employe = Employe.objects.get(matricule=self.cleaned_data['matricule'])
        user = User.objects.filter(email=employe.email_employe).first()
        employe_group, created = Group.objects.get_or_create(name='Employe')
        user.groups.add(employe_group)
        
        # Set the password using make_password to hash it securely
        user.password = make_password(self.cleaned_data['password1'])
        user.is_active = True  
        user.is_staff = True
        user.is_superuser = False

        if commit:
            employe.save()
            user.save()

        return employe

class ForgotPasswordForm(forms.Form):
    matricule = forms.IntegerField(
        widget=forms.TextInput(attrs={'placeholder': 'Matricule'})
    )
    email = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Email'})
    )
    
    def __init__(self, *args, **kwargs):
        super(EmployeRegistrationForm, self).__init__(*args, **kwargs)
        
        # Remove labels for fields
        for field_name, field in self.fields.items():
            field.label = ''

    def clean_matricule(self):
        matricule = self.cleaned_data['matricule']

        existing_employe = Employe.objects.filter(matricule=matricule).first()

        if existing_employe:
            existing_user = User.objects.filter(username__iexact=f"{existing_employe.nom_employe.split()[0]}{existing_employe.matricule}").first()

            if not existing_user:
                raise forms.ValidationError("il n'y a pas un compte existant pour ce employé.")
        else:
            raise forms.ValidationError("Il n'y a pas un employé de cette matricule.")

        return matricule
from django_select2.forms import ModelSelect2Widget

class ProjetNameForm(forms.ModelForm):
    projet_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter un nom de projet pour une analyse spécifié...'}),
    )

    class Meta:
        model = EtatProjet
        fields = ['projet_name']

class ProjetNameForm2(forms.ModelForm):
    projet_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter un nom de projet ...'}),
    )

    class Meta:
        model = EtatProjet
        fields = ['projet_name']

class TacheNameForm(forms.ModelForm):
    nom_tache = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter un nom de tache pour une analyse spécifié...'}),
    )

    class Meta:
        model = Tache
        fields = ['nom_tache']