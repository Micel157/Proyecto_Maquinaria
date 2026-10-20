from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    # Muestra el formulario y comprueba las credenciales.
    path(
        'login/',
        LoginView.as_view(template_name='usuarios/login.html'),
        name='login',
    ),

    # Abre el panel; la vista exige una sesión activa.
    path('dashboard/', views.dashboard, name='dashboard'),

    # Operaciones provisionales de consulta y registro de maquinaria.
    path('maquinaria/', views.maquinaria_lista, name='maquinaria_lista'),
    path(
        'maquinaria/registrar/',
        views.maquinaria_registrar,
        name='maquinaria_registrar',
    ),
    path(
        'maquinaria/<uuid:maquinaria_id>/',
        views.maquinaria_detalle,
        name='maquinaria_detalle',
    ),

    # Cierra la sesión y redirige al login.
    path(
        'logout/',
        LogoutView.as_view(next_page='login'),
        name='logout',
    ),
]