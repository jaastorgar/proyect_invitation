from django.urls import path
from . import views

urlpatterns = [
    # Invitación personalizada con token UUID
    path('invitacion/<uuid:token>/', views.invitacion_view, name='invitacion_personalizada'),
    path('api/responder/<uuid:token>/', views.responder_rsvp, name='responder_rsvp'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('api/dashboard/', views.dashboard_api_view, name='dashboard_api'),
    path('crear-invitacion/', views.crear_invitacion_view, name='crear_invitacion'),
    path('crear-admin-temp/', views.crear_superusuario_temporal, name='crear_admin_temp'),
]