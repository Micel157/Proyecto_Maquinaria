from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect, render

from .forms import MaquinariaForm
from .roles import permisos_panel
from .maquinaria_store import (
    crear_maquinaria,
    obtener_maquinaria,
    obtener_maquinarias,
)


# Exige una sesión activa para acceder al dashboard.
@login_required
def dashboard(request):
    # Muestra la plantilla del dashboard.
    return render(request, 'usuarios/dashboard.html')


@login_required
def maquinaria_lista(request):
    if not permisos_panel(request.user)['puede_consultar_maquinaria']:
        raise PermissionDenied
    maquinarias = obtener_maquinarias()
    consulta = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    if consulta:
        consulta_normalizada = consulta.casefold()
        maquinarias = [
            maquinaria
            for maquinaria in maquinarias
            if any(
                consulta_normalizada in str(maquinaria[campo]).casefold()
                for campo in ('codigo', 'nombre', 'categoria', 'numero_serie')
            )
        ]
    if estado:
        maquinarias = [
            maquinaria
            for maquinaria in maquinarias
            if maquinaria['estado'] == estado
        ]

    return render(
        request,
        'usuarios/maquinaria_lista.html',
        {
            'maquinarias': maquinarias,
            'consulta': consulta,
            'estado_seleccionado': estado,
            'estados': MaquinariaForm.ESTADOS,
        },
    )


@login_required
def maquinaria_registrar(request):
    if not permisos_panel(request.user)['puede_registrar_maquinaria']:
        raise PermissionDenied
    if request.method == 'POST':
        form = MaquinariaForm(request.POST)
        if form.is_valid():
            maquinaria = crear_maquinaria(form.cleaned_data)
            messages.success(request, 'La maquinaria se registró correctamente.')
            return redirect('maquinaria_detalle', maquinaria_id=maquinaria['id'])
    else:
        form = MaquinariaForm()

    return render(request, 'usuarios/maquinaria_form.html', {'form': form})


@login_required
def maquinaria_detalle(request, maquinaria_id):
    if not permisos_panel(request.user)['puede_consultar_maquinaria']:
        raise PermissionDenied
    maquinaria = obtener_maquinaria(str(maquinaria_id))
    if maquinaria is None:
        raise Http404('No existe esa maquinaria.')
    return render(
        request,
        'usuarios/maquinaria_detalle.html',
        {'maquinaria': maquinaria},
    )
