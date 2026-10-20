from .roles import permisos_panel


def acceso_panel(request):
    if not request.user.is_authenticated:
        return {}
    return permisos_panel(request.user)
