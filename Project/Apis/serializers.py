from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from Gestion_projet.models import Employe,Notification,Projet,Marchet,MaitreOuvrage,Tache,Comission,Document,SuiviTache,SuiviIncident,EtatTache,Incident


class Todoserializer(serializers.ModelSerializer):
    class Meta:
        fields = ['id', 'username', 'email']
        
        model = User  

class Employeserializer(serializers.ModelSerializer):
    class Meta :
        fields = '__all__'
        model = Employe
        
class Notificationserializer(serializers.ModelSerializer):
    class Meta :
        fields = '__all__'
        model = Notification

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['email',]

        model = User



class MaitreOuvrageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = MaitreOuvrage
       # Add the required fields


class MarchetSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Marchet
        extra_kwargs = {
            'lib_mouvrage': {'required': False},
            'details': {'required': False},
         
        }

 
class ProjetSerializer(serializers.ModelSerializer):
    maitreOuvrage = MaitreOuvrageSerializer()
    marchet = MarchetSerializer()
    chefProjet = Employeserializer() 
    class Meta :
        fields = '__all__'
        model = Projet

    

class TacheSerializer(serializers.ModelSerializer):

    class Meta :
        fields = '__all__'
        model = Tache

class SuivitacheSerializer(serializers.ModelSerializer):
    class Meta :
        fields = '__all__'
        model = SuiviTache

class checktacheSerializer(serializers.ModelSerializer):
    class Meta :
        fields = '__all__'
        model = EtatTache

class incidentSerializer(serializers.ModelSerializer):
    agentDeclencheur = Employeserializer() 
    tache = TacheSerializer() 
    class Meta :
        fields = '__all__'
        model = Incident

class SuiviincidentSerializer(serializers.ModelSerializer):
    class Meta :
        fields = '__all__'
        model = SuiviIncident

class CommisionSerializer(serializers.ModelSerializer):
    projet = ProjetSerializer()
    tache = TacheSerializer()
    president = Employeserializer() 
    employes = Employeserializer(many=True)
    class Meta :
        fields = '__all__'
        model = Comission

class DocumentSerializer(serializers.ModelSerializer):


    class Meta :
        fields = '__all__'
        model = Document
        extra_kwargs = {
            'tache': {'required': False},
        }

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=4)

    def validate(self, data):
        token = self.context.get("kwargs").get("token")
        encoded_pk = self.context.get("kwargs").get("encoded_pk")

        if token is None:
            raise serializers.ValidationError("Missing token.")
        if encoded_pk is None:
            raise serializers.ValidationError("Missing encoded_pk.")

        pk = urlsafe_base64_decode(encoded_pk).decode()
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            raise serializers.ValidationError("utilisateur incvalide")

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError("lien invalide")

        return data  # Return validated data

    def create(self, validated_data):
        encoded_pk = self.context.get("kwargs").get("encoded_pk")
        pk = urlsafe_base64_decode(encoded_pk).decode()
        
        password = validated_data.get('password')

        user = User.objects.get(pk=pk)
        user.set_password(password)
        user.save()
        return validated_data
