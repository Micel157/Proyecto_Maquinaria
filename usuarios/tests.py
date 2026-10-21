from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse

from .models import Categoria, Maquinaria, Unidad


def crear_unidad(codigo='RET-001', serie='SERIE-001', estado='Disponible'):
    categoria, _ = Categoria.objects.get_or_create(nombre='Construcción')
    maquinaria = Maquinaria.objects.create(
        categoria=categoria,
        codigo=codigo,
        nombre='Retroexcavadora',
        marca='Marca',
        modelo='Modelo X',
        costo_adquisicion='125000.00',
        tarifa_diaria='150.00',
        tarifa_semanal='900.00',
        tarifa_mensual='3000.00',
        deposito_garantia='500.00',
    )
    return Unidad.objects.create(
        maquinaria=maquinaria,
        numero_serie=serie,
        estado=estado,
        horas_uso='12.5',
    )


class MaquinariaViewsTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_superuser(
            username='prueba', password='ClaveSegura123!'
        )
        self.client.force_login(usuario)
        self.datos = {
            'codigo': 'RET-001', 'nombre': 'Retroexcavadora',
            'categoria': 'Construcción', 'marca': 'Marca', 'modelo': 'Modelo X',
            'costo_adquisicion': '125000.00', 'tarifa_diaria': '150.00',
            'tarifa_semanal': '900.00', 'tarifa_mensual': '3000.00',
            'deposito_garantia': '500.00', 'numero_serie': 'SERIE-001',
            'estado': 'Disponible', 'horas_uso': '12.5',
            'fecha_adquisicion': '',
        }

    def test_maquinaria_pages_require_login(self):
        self.client.logout()
        respuesta = self.client.get(reverse('maquinaria_lista'))
        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={reverse('maquinaria_lista')}",
        )

    def test_admin_can_register_filter_and_open_details(self):
        respuesta = self.client.post(reverse('maquinaria_registrar'), self.datos)
        self.assertEqual(respuesta.status_code, 302)
        unidad = Unidad.objects.select_related('maquinaria').get()
        self.assertRedirects(
            respuesta,
            reverse('maquinaria_detalle', kwargs={'maquinaria_id': unidad.id}),
        )
        for filtros in ({'q': 'retro'}, {'q': 'SERIE-001'}, {'estado': 'Disponible'}):
            with self.subTest(filtros=filtros):
                self.assertContains(
                    self.client.get(reverse('maquinaria_lista'), filtros),
                    'Retroexcavadora',
                )
        self.assertNotContains(
            self.client.get(reverse('maquinaria_lista'), {'estado': 'Mantenimiento'}),
            'SERIE-001',
        )
        detalle = self.client.get(reverse('maquinaria_detalle', args=[unidad.id]))
        self.assertContains(detalle, 'SERIE-001')
        self.assertContains(detalle, 'Construcción')

    def test_invalid_input_displays_field_validation(self):
        datos_invalidos = {**self.datos, 'tarifa_diaria': '0', 'numero_serie': ''}
        respuesta = self.client.post(reverse('maquinaria_registrar'), datos_invalidos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, '0.01')
        self.assertContains(respuesta, 'obligatorio')
        self.assertFalse(Unidad.objects.exists())

    def test_duplicate_code_and_serial_are_rejected(self):
        self.client.post(reverse('maquinaria_registrar'), self.datos)
        respuesta_codigo = self.client.post(
            reverse('maquinaria_registrar'),
            {**self.datos, 'numero_serie': 'SERIE-002'},
        )
        self.assertContains(
            respuesta_codigo, 'Ya existe una maquinaria con este código.'
        )
        respuesta_serie = self.client.post(
            reverse('maquinaria_registrar'),
            {**self.datos, 'codigo': 'RET-002'},
        )
        self.assertContains(
            respuesta_serie, 'Ya existe una maquinaria con este número de serie.'
        )
        self.assertEqual(Unidad.objects.count(), 1)

    def test_missing_detail_returns_not_found(self):
        self.assertEqual(
            self.client.get(reverse('maquinaria_detalle', args=[999999])).status_code,
            404,
        )


class SupervisorTests(TestCase):
    def setUp(self):
        self.supervisor = get_user_model().objects.create_user(
            username='supervisor', first_name='Ana', last_name='Pérez',
            password='ClaveSupervisor123!',
        )
        self.supervisor.groups.add(Group.objects.create(name='Supervisor'))
        self.admin = get_user_model().objects.create_superuser(
            username='admin', password='ClaveAdmin123!'
        )

    def test_shared_login_displays_independent_roles(self):
        for usuario, clave, nombre, rol in (
            (self.supervisor, 'ClaveSupervisor123!', 'Ana Pérez', 'Supervisor'),
            (self.admin, 'ClaveAdmin123!', 'admin', 'Administrador'),
        ):
            with self.subTest(rol=rol):
                respuesta = self.client.post(
                    reverse('login'),
                    {'username': usuario.username, 'password': clave},
                    follow=True,
                )
                self.assertRedirects(respuesta, reverse('dashboard'))
                self.assertContains(respuesta, nombre)
                self.assertContains(respuesta, f'Panel de {rol}')
                if rol == 'Supervisor':
                    self.assertNotContains(respuesta, reverse('maquinaria_registrar'))
                else:
                    self.assertContains(respuesta, reverse('maquinaria_registrar'))
                self.client.post(reverse('logout'))

    def test_supervisor_can_consult_but_cannot_register_by_direct_url(self):
        unidad = crear_unidad()
        self.client.force_login(self.supervisor)
        lista = self.client.get(reverse('maquinaria_lista'))
        self.assertEqual(lista.status_code, 200)
        self.assertNotContains(lista, reverse('maquinaria_registrar'))
        self.assertEqual(
            self.client.get(reverse('maquinaria_detalle', args=[unidad.id])).status_code,
            200,
        )
        for metodo in (self.client.get, self.client.post):
            with self.subTest(metodo=metodo.__name__):
                self.assertEqual(
                    metodo(reverse('maquinaria_registrar'), self._datos_post()).status_code,
                    403,
                )
        self.assertEqual(Unidad.objects.count(), 1)
        self.assertRedirects(
            self.client.get(reverse('admin:index')), '/admin/login/?next=/admin/'
        )

    def test_unassigned_user_has_no_maquinaria_access(self):
        usuario = get_user_model().objects.create_user(username='sinrol')
        self.client.force_login(usuario)
        self.assertContains(self.client.get(reverse('dashboard')), 'Sin rol asignado')
        for url in (
            reverse('maquinaria_lista'), reverse('maquinaria_registrar'),
            reverse('maquinaria_detalle', args=[999999]),
        ):
            self.assertEqual(self.client.get(url).status_code, 403)

    def test_command_creates_account_and_preserves_password_on_rerun(self):
        call_command('crear_supervisor', 'nuevo', nombre='Luis', stdout=StringIO())
        usuario = get_user_model().objects.get(username='nuevo')
        self.assertFalse(usuario.has_usable_password())
        self.assertFalse(usuario.is_staff)
        self.assertFalse(usuario.is_superuser)
        self.assertTrue(usuario.groups.filter(name='Supervisor').exists())
        usuario.set_password('NuevaClaveSegura123!')
        usuario.save()
        call_command('crear_supervisor', 'nuevo', stdout=StringIO())
        usuario.refresh_from_db()
        self.assertTrue(usuario.check_password('NuevaClaveSegura123!'))

    def test_command_never_changes_admin(self):
        with self.assertRaises(CommandError):
            call_command('crear_supervisor', 'admin', stdout=StringIO())
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_staff)
        self.assertTrue(self.admin.is_superuser)
        self.assertFalse(self.admin.groups.filter(name='Supervisor').exists())

    @staticmethod
    def _datos_post():
        return {
            'codigo': 'PROHIBIDO', 'nombre': 'No debe guardarse',
            'categoria': 'Prueba', 'costo_adquisicion': '1',
            'tarifa_diaria': '1', 'tarifa_semanal': '1',
            'tarifa_mensual': '1', 'deposito_garantia': '0',
            'numero_serie': 'PROHIBIDO', 'estado': 'Disponible',
            'horas_uso': '0',
        }
