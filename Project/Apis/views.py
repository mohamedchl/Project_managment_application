from rest_framework import generics,status,response,serializers
from django.contrib.auth.models import User  # Import the User model
from .serializers import Todoserializer,EmailSerializer,ResetPasswordSerializer,Employeserializer,Notificationserializer,ProjetSerializer,TacheSerializer,CommisionSerializer,DocumentSerializer,SuivitacheSerializer,checktacheSerializer,incidentSerializer,SuiviincidentSerializer
from django.contrib.auth import authenticate,get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.decorators import authentication_classes, permission_classes    
from django.shortcuts import get_object_or_404,redirect,render
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from .forms import ResetPasswordForm
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.http import Http404
from Gestion_projet.models import Employe,Notification,Projet,Comission,Document,Tache,SuiviTache,Incident,SuiviIncident,EtatTache



class ListTodo(generics.ListCreateAPIView):
    queryset = User.objects.all()  # Queryset to retrieve all users
    serializer_class = Todoserializer

class DetailsTodo(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()  # Queryset to retrieve all users
    serializer_class = Todoserializer


class ResetPassword(generics.GenericAPIView):
    serializer_class = EmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data["email"]
        user = User.objects.filter(email=email).first()

        if user:
            encoded_pk = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)
            reset_url = reverse("reset_password_form", kwargs={"encoded_pk": encoded_pk, "token": token})
            reset_url = f"http://127.0.0.1:8000{reset_url}"

            # Send the email to the user's email address
            subject = 'Password Reset'
            message = f'Click ici pour Recuperer votre mot de passe: {reset_url}'
            from_email = 'your_email@gmail.com'
            recipient_list = [user.email]
            send_mail(subject, message, from_email, recipient_list)

            return response.Response(
                {"message": "Password reset link has been sent to your email."},
                status=status.HTTP_200_OK
            )
        else:
            return response.Response(
                {"message": "User doesn't exist"},
                status=status.HTTP_400_BAD_REQUEST
            )


    
class ResetPasswordFormView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def get(self, request, *args, **kwargs):

        serializer = self.serializer_class(context={"kwargs": kwargs})
        try:
            serializer.validate(self.request.data)
            # Assuming you have a ResetPasswordForm class
            form = ResetPasswordForm()
            return render(request, 'reset_password_form.html', {'form': form})
        except serializers.ValidationError as e:
            return render(request, 'reset_password_fail.html', {'errors': e.detail})

    def post(self, request, *args, **kwargs):
   
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            try:
                serializer = self.serializer_class(
                    data=request.data, context={"kwargs": kwargs}
                )
                serializer.is_valid(raise_exception=True)

                # Perform the password reset logic
                serializer.save()

                return render(request, 'reset_password_success.html')
            except serializers.ValidationError as e:
                password_error = None
                if 'password' in e.detail and any(error == "Ensure this field has at least 4 characters." for error in e.detail['password']):
                    password_error = "Le mot de passe doit comporter au moins 5 caractères."
                return render(request, 'reset_password_form.html', {'form': form, 'password_error': password_error, 'errors': e.detail})

        return render(request, 'reset_password_form.html', {'form': form})
    
def  reset_password_success(request):
       return render(request, 'reset_password_success.html')

def  reset_password_fail(request):
       return render(request, 'reset_password_fail.html')

from rest_framework.decorators import api_view
from rest_framework.response import Response
 
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)

    if not user:
        return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    token, created_token  = Token.objects.get_or_create(user=user)
    serializer = Todoserializer(user)

    return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_200_OK)


class userview(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = Todoserializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        id = self.kwargs['id']
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return response(status=status.HTTP_400_BAD_REQUEST) 
        
class employeview(generics.RetrieveUpdateDestroyAPIView):
    queryset = Employe.objects.all()
    serializer_class = Employeserializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        id = self.kwargs['id']
        try:
            user= User.objects.get(id=id)
            employe = Employe.objects.get(email_employe=user.email)
            return employe
        except Employe.DoesNotExist or User.DoesNotExist:
            return response(status=status.HTTP_400_BAD_REQUEST) 
        
class Notificationview(generics.ListAPIView):

    queryset = Notification.objects.all()
    serializer_class = Notificationserializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):

        employee_id = self.kwargs['id']

        try:
            # Filter notifications for the specified employee
            notifications = Notification.objects.filter(employe__id_employe=employee_id)

            # Check if any notifications exist for the employee
            if not notifications.exists():
                raise Http404("Notification does not exist for this employee.")

            # Print retrieved notifications (for debugging)
            for notification in notifications:
                print(notification.employe)  # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class NotificationDelete(generics.RetrieveDestroyAPIView):
    queryset = Notification.objects.all()
    serializer_class = Notificationserializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id_notification'

    def delete(self, request, *args, **kwargs):
        id_employe = self.kwargs['id_employe']
        id_notification = self.kwargs['id_notification']

        try:
            notification = Notification.objects.get(id_notification=id_notification, employe__id_employe=id_employe)
            employe1 = Employe.objects.get(id_employe=id_employe)
            notification.employe.remove(employe1)
            if not notification.employe.exists():
                notification.delete()
            return Response({'message': 'Notification successfully deleted'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'message': 'Notification does not exist for this employee'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateNotificationNotSeenView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:    
            id = self.kwargs['id_employe']
            employe = Employe.objects.get(id_employe=id)
            employe.notificationNotSeen = 0
            employe.save()
            return Response(status=status.HTTP_200_OK)
        except Employe.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
class Projectsview(generics.ListAPIView):
    """
    API endpoint for retrieving all notifications for a specific employee.
    """
    queryset = Projet.objects.all()
    serializer_class = ProjetSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        employee_id = self.kwargs['id']

        try:
            # Filter projects for the specified employee
            projets = Projet.objects.filter(employe__id_employe=employee_id)

            # Check if any projects exist for the employee
            if not projets.exists():
                return Response("no data", status=status.HTTP_200_OK)

            # Add hasincident field to each project
            serialized_projets = []
            for projet in projets:
                incidents = Incident.objects.filter(projet=projet, employe=employee_id)
                serialized_projet = self.get_serializer(projet).data
                serialized_projet['hasincident'] = incidents.exists()
                serialized_projets.append(serialized_projet)

            return Response(serialized_projets, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class Commisionsview(generics.ListAPIView):
    """
    API endpoint for retrieving all notifications for a specific employee.
    """
    queryset = Comission.objects.all()
    serializer_class = CommisionSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
  
        employee_id = self.kwargs['id']

        try:
            # Filter notifications for the specified employee
            commisions = Comission.objects.filter(employes__id_employe=employee_id)

            # Check if any notifications exist for the employee
            if not commisions.exists():
                 return Response("no data" , status=status.HTTP_200_OK)

            # Print retrieved notifications (for debugging)
     # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(commisions, many=True)
            return Response(serializer.data , status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class Commisionprojetsview(generics.ListAPIView):
    """
    API endpoint for retrieving all notifications for a specific employee.
    """
    queryset = Comission.objects.all()
    serializer_class = CommisionSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
  
        employee_id = self.kwargs['id']
        projet_id = self.kwargs['projet_id']

        try:
            # Filter notifications for the specified employee
            commisions = Comission.objects.filter(employes__id_employe=employee_id,projet = projet_id)

            # Check if any notifications exist for the employee
            if not commisions.exists():
                 return Response("no data" , status=status.HTTP_200_OK)

            # Print retrieved notifications (for debugging)
     # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(commisions, many=True)
            return Response(serializer.data , status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.http import HttpResponse, StreamingHttpResponse


class Commisionsdownloadview(generics.RetrieveAPIView):
    queryset = Comission.objects.all()
    serializer_class = CommisionSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id_comission'



    def get(self, request, *args, **kwargs):
        commision_id = self.kwargs['id_comission']
        try:
            comission = Comission.objects.get(id_comission=commision_id)
            if comission.PV:
                file_path = comission.PV.path
                with open(file_path, 'rb') as file:
                        response = HttpResponse(file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(comission.PV.name)
                        return response
            else:
                return Response("File not found", status=status.HTTP_404_NOT_FOUND)

        except Comission.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
class Documentsview(generics.ListAPIView):
    """
    API endpoint for retrieving all notifications for a specific employee.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
  
        employee_id = self.kwargs['id']

        try:
            # Filter notifications for the specified employee
            Documents = Document.objects.filter(employe__id_employe=employee_id)

            # Check if any notifications exist for the employee
            if not Documents.exists():
                 return Response("no data" , status=status.HTTP_200_OK)

            # Print retrieved notifications (for debugging)
     # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(Documents, many=True)
            return Response(serializer.data , status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from django.http import HttpResponse, StreamingHttpResponse


class Documentsdownloadview(generics.RetrieveAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id_document'



    def get(self, request, *args, **kwargs):
        Document_id = self.kwargs['id_document']
        try:
            document = Document.objects.get(id_document=Document_id)
      
            file_path = document.doc.path
            with open(file_path, 'rb') as file:
                        response = HttpResponse(file.read(), content_type='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename="{0}"'.format(document.doc.name)
                        return response
       

        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

from rest_framework.exceptions import APIException
import base64
from django.core.files.base import ContentFile

from datetime import datetime

class DocumentCreateView(generics.CreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        base64_file = request.data.get('doc')  # Get the base64 encoded file string from the request data
        if base64_file:
            # Decode the base64 file string
            file_data = base64.b64decode(base64_file)
            file_name = request.data.get('fileName')     
            document = ContentFile(file_data, name=file_name)
            request.data['doc'] = document
        
        raw_date = request.data.get('date')
        if raw_date:
            # Extract only the year, month, and day from the received date
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            # Convert the date object back to a string in the desired format
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date'] = formatted_date
        
        print(request.data.get('date'))

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            error_message = "Serializer errors: " + str(serializer.errors)
            raise APIException(detail=error_message, code=status.HTTP_400_BAD_REQUEST)
        
class DocumentDelete(generics.RetrieveDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id_Document'

    def delete(self, request, *args, **kwargs):
        id_document = self.kwargs['id_Document']
       

        try:
            document = Document.objects.get(id_document=id_document)
            document.delete()
            return Response({'message': 'Document successfully deleted'}, status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response({'message': 'document does not exist for this employee'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class DocumentUpdateView(generics.UpdateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        id_documenti = self.kwargs['document_id']
        try:
            document = Document.objects.get(id_document=id_documenti)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        base64_file = request.data.get('doc')
        if base64_file:
            file_data = base64.b64decode(base64_file)
            file_name = request.data.get('fileName')     
            file = ContentFile(file_data, name=file_name)
            request.data['doc'] = file
        else :
            print('rah faregh')
            file1 = Document.objects.get(id_document=id_documenti)
            request.data['doc'] = file1.doc

        raw_date = request.data.get('date')
        if raw_date:
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date'] = formatted_date
        print(request.data.get('details'))
        serializer = self.get_serializer(document, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    

class TacheView(generics.ListAPIView):

    queryset = Tache.objects.all()
    serializer_class = TacheSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        employe = self.kwargs['employe_id']
        projet = self.kwargs['projet_id']
        try:
            taches = Tache.objects.filter(projet=projet, employe=employe)
            if not taches.exists():
                return Response("no data", status=status.HTTP_200_OK)

            serialized_taches = []
            for tache in taches:
                check = EtatTache.objects.filter(tache=tache.id_tache, employe=employe).last()
                is_checked = check.tache_finis if check else False
                serialized_tache = self.get_serializer(tache).data
                serialized_tache['ischecked'] = is_checked
                serialized_taches.append(serialized_tache)

            return Response(serialized_taches, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class chefsuivitacheview(generics.ListAPIView):

    queryset = SuiviTache.objects.all()
    serializer_class = SuivitacheSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):

        tach_id = self.kwargs['id']

        try:
            # Filter notifications for the specified employee
            suivi = SuiviTache.objects.filter(tache=tach_id)

            # Check if any notifications exist for the employee
            if not suivi.exists():
                raise Http404("Notification does not exist for this employee.")

            # Print retrieved notifications (for debugging)
        # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(suivi, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class suivitacheview(generics.ListAPIView):

    queryset = SuiviTache.objects.all()
    serializer_class = SuivitacheSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):

        tach_id = self.kwargs['id']
        employe_id = self.kwargs['employe_id']
        try:
            # Filter notifications for the specified employee
            suivi = SuiviTache.objects.filter(tache=tach_id,employe=employe_id)

            # Check if any notifications exist for the employee
            if not suivi.exists():
                raise Http404("suivi does not exist for this employee.")

            # Print retrieved notifications (for debugging)
        # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(suivi, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class suiviUpdateView(generics.UpdateAPIView):
    serializer_class = SuivitacheSerializer
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        id_suivi = self.kwargs['suivi_id']
        try:
            suivi = SuiviTache.objects.get(id_suivi=id_suivi)
        except SuiviTache.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        raw_date = request.data.get('date_suivi')
        
        if raw_date:
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date_suivi'] = formatted_date
            
        try :
            serializer = self.get_serializer(suivi, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
class suivitacheDelete(generics.RetrieveDestroyAPIView):
    queryset = SuiviTache.objects.all()
    serializer_class = SuivitacheSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id_suivitache'

    def delete(self, request, *args, **kwargs):
        id_suivitache = self.kwargs['id_suivitache']
       

        try:
            suivi = SuiviTache.objects.get(id_suivi=id_suivitache)
            suivi.delete()
            return Response({'message': 'Document successfully deleted'}, status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response({'message': 'document does not exist for this employee'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SuivitacheCreateView(generics.CreateAPIView):
    serializer_class = SuivitacheSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
       
        
        raw_date = request.data.get('date_suivi')
        if raw_date:
            # Extract only the year, month, and day from the received date
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            # Convert the date object back to a string in the desired format
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date_suivi'] = formatted_date
      
    
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            error_message = "Serializer errors: " + str(serializer.errors)
            raise APIException(detail=error_message, code=status.HTTP_400_BAD_REQUEST)
class employe_tachesview(generics.ListAPIView):
    """
    API endpoint for retrieving all employees for a specific task.
    """
    serializer_class = Employeserializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        tache_id = self.kwargs['tache_id']
        tache = get_object_or_404(Tache, id_tache=tache_id)
        return tache.employe.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if queryset.exists():
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response("No data", status=status.HTTP_200_OK)

     
from django.shortcuts import render

from django.http import JsonResponse

class checktache(generics.RetrieveAPIView):
    queryset = EtatTache.objects.all()
    serializer_class = checktacheSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):  # Add the request parameter
        tache_id = self.kwargs['id_tache']
        employe = self.kwargs['id_employe']  # Assuming employe is the authenticated user

        try:
            check = EtatTache.objects.filter(tache=tache_id, employe=employe).last()
            if check is None:
                return JsonResponse({'status': False}, status=status.HTTP_200_OK)
            elif check.tache_finis:
                return JsonResponse({'status': True}, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'status': False}, status=status.HTTP_200_OK)
        except EtatTache.DoesNotExist:
            return JsonResponse({'status': False}, status=status.HTTP_200_OK)
        
class checkCreateView(generics.CreateAPIView):
    serializer_class = checktacheSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
       
        
        raw_date = request.data.get('date')
        if raw_date:
            # Extract only the year, month, and day from the received date
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            # Convert the date object back to a string in the desired format
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date'] = formatted_date
      
    
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            error_message = "Serializer errors: " + str(serializer.errors)
            raise APIException(detail=error_message, code=status.HTTP_400_BAD_REQUEST)

        
class incidentView(generics.ListAPIView):

    queryset = Incident.objects.all()
    serializer_class = incidentSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        employe = self.kwargs['employe_id']
        projet = self.kwargs['projet_id']
        try:
            
            incidents = Incident.objects.filter(projet=projet,employe=employe)
            if incidents == None :
                 return Response("no data" , status=status.HTTP_404_NOT_FOUND)

            # Print retrieved notifications (for debugging)
     # Print employee details for each notification

            # Serialize all retrieved notifications for the response
            serializer = self.get_serializer(incidents, many=True)
            return Response(serializer.data , status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        

        
class suiviincidenteview(generics.ListAPIView):

    queryset = SuiviIncident.objects.all()
    serializer_class = SuiviincidentSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):

        incident_id = self.kwargs['id']
        employe_id = self.kwargs['employe_id']
        try:
            # Filter notifications for the specified employee
            suivi = SuiviIncident.objects.filter(incident=incident_id,employe=employe_id)

            # Check if any notifications exist for the employee
            if not suivi.exists():
                raise Http404("suivi does not exist for this employee.")

            serializer = self.get_serializer(suivi, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class suiviincidentUpdateView(generics.UpdateAPIView):
    serializer_class = SuiviincidentSerializer
    permission_classes = [AllowAny]

    def put(self, request, *args, **kwargs):
        id_suivi = self.kwargs['suivi_id']
        try:
            suivi = SuiviIncident.objects.get(id_suivi=id_suivi)
        except SuiviTache.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        raw_date = request.data.get('date_suivi')
        
        if raw_date:
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date_suivi'] = formatted_date
            print(request.data.get('date_suivi'))
        print(request.data.get('incident'))
        print(request.data.get('details'))
        print(request.data.get('employe'))
        print(request.data.get('id_suivi'))

        
        try :
            serializer = self.get_serializer(suivi, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
    
        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
class suiviincidentDelete(generics.RetrieveDestroyAPIView):
    queryset = SuiviIncident.objects.all()
    serializer_class = SuiviincidentSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id_suivicindent'

    def delete(self, request, *args, **kwargs):
        id_suivicindents = self.kwargs['id_suivicindent']
       

        try:
            suivi = SuiviIncident.objects.get(id_suivi=id_suivicindents)
            suivi.delete()
            return Response({'message': 'Document successfully deleted'}, status=status.HTTP_200_OK)
        except Document.DoesNotExist:
            return Response({'message': 'document does not exist for this employee'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SuiviincidentCreateView(generics.CreateAPIView):
    serializer_class = SuiviincidentSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
       
        
        raw_date = request.data.get('date_suivi')
        if raw_date:
            # Extract only the year, month, and day from the received date
            date = datetime.strptime(raw_date, '%Y-%m-%dT%H:%M:%S.%f').date()
            # Convert the date object back to a string in the desired format
            formatted_date = date.strftime('%Y-%m-%d')
            request.data['date_suivi'] = formatted_date
      
    
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            error_message = "Serializer errors: " + str(serializer.errors)
            raise APIException(detail=error_message, code=status.HTTP_400_BAD_REQUEST)
class lestachemere(generics.ListAPIView):
    serializer_class = TacheSerializer

    def get_queryset(self):
        tache_id = self.kwargs['id']
        tache = Tache.objects.get(id_tache=tache_id)
        tache_meres = self.get_tache_meres([tache])
        return tache_meres

    def get_tache_meres(self, taches, visited=None):
        if visited is None:
            visited = set()

        tache_meres = []
        for tache in taches:
            if tache.id_tache not in visited:
                visited.add(tache.id_tache)
                tache_meres.append(tache)
                if tache.tache_mere:
                    tache_meres += self.get_tache_meres([tache.tache_mere], visited)
        return tache_meres

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        
class LesSousTaches(generics.ListAPIView):
    serializer_class = TacheSerializer

    def get_queryset(self):
        tache_id = self.kwargs['id']
        tache = Tache.objects.get(id_tache=tache_id)
        sous_taches = [tache]  # Include the first task in the queryset
        sous_taches += list(tache.sous_taches.all())  # Include the subtasks
        return sous_taches

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404 as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)