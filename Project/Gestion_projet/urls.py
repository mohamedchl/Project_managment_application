from django.urls import path
from .views import affecter_projet,affecter_notification,affecter_tache,affecter_incident,projet_dashboard,tache_dashboard,tache_dashboardd
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.urls import reverse_lazy

urlpatterns = [
    path('register/', views.employe_registration_view, name='employe_registration'),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    path('custom-admin/', TemplateView.as_view(template_name='admin/admin.html'), name='custom_admin'),
    path('api/notification/count/', views.notification_count_api, name='notification_count_api'),
    path('api/mark-notifications-seen/', views.mark_notifications_seen, name='mark_notifications_seen'),
    path('api/mark-incidents-seen/', views.mark_incidents_seen, name='mark_incidents_seen'),
    path('api/check-user-is-employee/', views.check_user_is_employee, name='check_user_is_employee'),

    path('affecter-projet/', affecter_projet, name='affecter_projet'),
    path('affecter-notification/', affecter_notification, name='affecter_notification'),
    path('affecter-tache/', affecter_tache, name='affecter_tache'),
    path('affecter-incident/', affecter_incident, name='affecter_incident'),

    path('projet-dashboard/', projet_dashboard, name='projet_dashboard'),
    path('tache-dashboard/', tache_dashboard, name='tache_dashboard'),
    path('tache-dashboardd/<int:projet_id>/', tache_dashboardd, name='tache_dashboardd_with_id'),
    path('tache_dashboardd/', tache_dashboardd, name='tache_dashboardd'),
    #path('not/', views.test_request_view, name='test'),

    path('api/utilisation-ressource/<int:ressource_id>/', views.get_ressource_details, name='utilisation_ressource_api'),


]
