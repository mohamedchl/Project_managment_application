from django.urls import path, re_path,include
from .views import ListTodo, DetailsTodo
from . import views
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated

urlpatterns = [
    path('', ListTodo.as_view()),
    path('<int:pk>', DetailsTodo.as_view()),
   
    path('reset_password/',views.ResetPassword.as_view(),name="reset_password"),
     path('reset_password_form/<str:encoded_pk>/<str:token>', views.ResetPasswordFormView.as_view(), name='reset_password_form'),
      re_path('reset_password_success',views.reset_password_success),
        re_path('reset_password_fail',views.reset_password_fail),

       re_path('login',views.login),
      path('user/<int:id>',views.userview.as_view()),
         path('employe/<int:id>',views.employeview.as_view()),
           path('notification/<int:id>',views.Notificationview.as_view()),
            path('projects/<int:id>',views.Projectsview.as_view()),
           path('deletnotification/<int:id_notification>/<int:id_employe>',views.NotificationDelete.as_view()),
               
               path('updatenotificationseenview/<int:id_employe>',views.UpdateNotificationNotSeenView.as_view()),
                           path('commisions/<int:id>',views.Commisionsview.as_view()),
    path('commisions/<int:id_comission>/download_pv',views.Commisionsdownloadview.as_view()),
                               path('commisions_projet/<int:id>/<int:projet_id>',views.Commisionprojetsview.as_view()),

                               path('Documents/<int:id>',views.Documentsview.as_view()),
                                 path('Documents/<int:id>/create',views.DocumentCreateView.as_view()),
    path('Documents/<int:id_document>/download_doc',views.Documentsdownloadview.as_view()),
               path('deletdocument/<int:id_Document>',views.DocumentDelete.as_view()),
                   path('Documents/<int:document_id>/update',views.DocumentUpdateView.as_view()),
                              path('taches/<int:employe_id>/<int:projet_id>',views.TacheView.as_view()),
                                                            path('suivis_chef/<int:id>/',views.chefsuivitacheview.as_view()),
                                                                                          path('suivis/<int:id>/<int:employe_id>',views.suivitacheview.as_view()),
                 path('deletsuivi/<int:id_suivitache>',views.suivitacheDelete.as_view()),
                                    path('suivis/<int:suivi_id>/update',views.suiviUpdateView.as_view()),
                                                                        path('suivis/create',views.SuivitacheCreateView.as_view()),
                                                                           path('employe_tache/<int:tache_id>',views.employe_tachesview.as_view()),
                                                                           path('check_tache/<int:id_tache>/<int:id_employe>',views.checktache.as_view()),
                                                                            path('check_tache/create',views.checkCreateView.as_view()),
                              path('incidents/<int:employe_id>/<int:projet_id>',views.incidentView.as_view()),
                               path('suivis_incident/<int:id>/<int:employe_id>',views.suiviincidenteview.as_view()),
                 path('deletsuivicident/<int:id_suivicindent>',views.suiviincidentDelete.as_view()),
                             path('suivicident/create',views.SuiviincidentCreateView.as_view()),
                              path('suivicident/<int:suivi_id>/update',views.suiviincidentUpdateView.as_view()),
                              path('List_tachemere/<int:id>',views.lestachemere.as_view()),
                                        path('List_soustache/<int:id>',views.LesSousTaches.as_view()),








]
