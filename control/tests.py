from datetime import timedelta
from decimal import Decimal
from io import BytesIO, StringIO

from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from .forms import OftalmologoForm, PacienteForm, ProductoForm
from .models import (
    ArqueoCaja,
    Categoria,
    Cita,
    ConsultaMedica,
    DetalleVenta,
    Oftalmologo,
    Paciente,
    ParametrosSistema,
    Producto,
    ProcedimientoOftalmologico,
    RecetaOftalmologica,
    User,
    Venta,
)


class DashboardTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.paciente = Paciente.objects.create(
            nombre='María',
            apellido='Ríos',
            dni='11111111',
            fecha_nacimiento=today - timedelta(days=365 * 30),
        )
        self.oftalmologo = Oftalmologo.objects.create(
            nombre='Ana',
            apellido='Vega',
            dni='22222222',
            numero_colegiatura='DASH-3001',
        )
        self.cita = Cita.objects.create(
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            fecha_hora=timezone.now(),
            motivo_consulta='Control visual',
        )
        self.segunda_cita = Cita.objects.create(
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            fecha_hora=timezone.now() + timedelta(minutes=30),
            motivo_consulta='Evaluación de vista',
        )
        paciente_cancelado = Paciente.objects.create(
            nombre='Luis',
            apellido='Salas',
            dni='11111112',
            fecha_nacimiento=today - timedelta(days=365 * 25),
        )
        Cita.objects.create(
            paciente=paciente_cancelado,
            oftalmologo=self.oftalmologo,
            fecha_hora=timezone.now(),
            motivo_consulta='Cita cancelada',
            estado=Cita.Estado.CANCELADA,
        )
        self.admin = User.objects.create_user(
            username='dashboard-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
        )

    def test_dashboard_shows_distinct_patients_queue_and_refraction_link(self):
        consulta = ConsultaMedica.objects.create(
            cita=self.cita,
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            fecha_atencion=timezone.now(),
            sintomas='Visión borrosa',
            diagnostico='Miopía',
        )
        receta = RecetaOftalmologica.objects.create(
            consulta=consulta,
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            esfera_od=Decimal('-1.00'),
            cilindro_od=Decimal('0.00'),
            eje_od=0,
            esfera_oi=Decimal('-1.00'),
            cilindro_oi=Decimal('0.00'),
            eje_oi=0,
        )
        Venta.objects.create(
            paciente=self.paciente,
            usuario=self.admin,
            subtotal=Decimal('72.50'),
            total=Decimal('72.50'),
            metodo_pago=Venta.MetodoPago.EFECTIVO,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('control:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pacientes_programados_hoy'], 1)
        self.assertEqual(response.context['citas_pendientes_hoy'], 2)
        self.assertEqual(response.context['ventas_hoy'], Decimal('72.50'))
        self.assertEqual(
            list(response.context['cola_espera'].values_list('pk', flat=True)),
            [self.cita.pk, self.segunda_cita.pk],
        )
        self.assertContains(response, 'No registrado')
        self.assertContains(
            response,
            reverse('control:receta_print', args=[receta.pk]),
        )

    def test_dashboard_hides_clinical_actions_from_cashiers(self):
        cashier = User.objects.create_user(
            username='dashboard-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        self.client.force_login(cashier)

        response = self.client.get(reverse('control:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Ficha')
        self.assertNotContains(response, 'Atender')
        self.assertNotContains(
            response,
            reverse('control:recetas_list'),
        )


class OftalmologoManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='ophthalmologist-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
        )
        self.oftalmologo = Oftalmologo.objects.create(
            nombre='Elena',
            apellido='Paredes',
            dni='33333333',
            numero_colegiatura='CMP-2001',
        )

    def test_admin_can_register_oftalmologo(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:oftalmologo_create'),
            {
                'nombre': 'Carlos',
                'apellido': 'Vargas',
                'dni': '44444444',
                'numero_colegiatura': 'CMP-2002',
                'especialidad': 'Oftalmología General',
                'telefono': '',
                'email': '',
                'horario_atencion': 'Lunes a viernes',
            },
        )

        self.assertRedirects(response, reverse('control:oftalmologos_list'))
        self.assertTrue(
            Oftalmologo.objects.filter(
                numero_colegiatura='CMP-2002',
            ).exists(),
        )

    def test_admin_can_search_edit_and_permanently_delete_an_oftalmologo(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('control:oftalmologos_list'),
            {'q': 'CMP-2001'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CMP-2001')
        self.assertContains(response, 'Editar')

        response = self.client.post(
            reverse('control:oftalmologo_update', args=[self.oftalmologo.pk]),
            {
                'nombre': 'Elena',
                'apellido': 'Paredes',
                'dni': '33333333',
                'numero_colegiatura': 'CMP-2001',
                'especialidad': Oftalmologo.Especialidad.RETINA_GLAUCOMA,
                'telefono': '',
                'email': '',
                'horario_atencion': '',
            },
        )
        self.assertRedirects(response, reverse('control:oftalmologos_list'))
        self.oftalmologo.refresh_from_db()
        self.assertEqual(
            self.oftalmologo.especialidad,
            Oftalmologo.Especialidad.RETINA_GLAUCOMA,
        )
        response = self.client.post(
            reverse(
                'control:oftalmologo_delete',
                args=[self.oftalmologo.pk],
            ),
        )
        self.assertRedirects(response, reverse('control:oftalmologos_list'))
        self.assertFalse(
            Oftalmologo.objects.filter(pk=self.oftalmologo.pk).exists(),
        )

    def test_cashier_cannot_manage_oftalmologos(self):
        cashier = User.objects.create_user(
            username='ophthalmologist-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        self.client.force_login(cashier)

        response = self.client.get(reverse('control:oftalmologos_list'))

        self.assertRedirects(response, reverse('control:dashboard'))
        response = self.client.get(reverse('control:dashboard'))
        self.assertNotContains(response, 'Oftalmólogos')


class RoleNavigationTests(TestCase):
    def test_only_administrator_and_cashier_roles_are_available(self):
        self.assertEqual(
            set(User.Rol.values),
            {'ADMINISTRADOR', 'CAJERO_VENDEDOR'},
        )

    def test_administrator_sees_management_and_cashier_only_operational_links(self):
        admin = User.objects.create_user(
            username='navigation-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(admin)
        response = self.client.get(reverse('control:dashboard'))

        self.assertContains(response, 'Gestión de usuarios')
        self.assertContains(response, 'Configuración')
        self.assertContains(response, 'Oftalmólogos')
        self.assertContains(response, 'Productos')
        self.assertContains(response, 'Inventario')
        self.assertContains(response, 'Recetas')
        self.assertContains(response, 'Oftalmólogos')
        self.assertContains(response, 'Ventas / POS')
        self.assertNotContains(response, 'Punto de venta')
        self.assertContains(response, reverse('control:ventas_list'))
        self.assertContains(response, reverse('control:usuarios_list'))
        self.assertContains(response, reverse('control:configuracion'))
        self.assertContains(response, reverse('control:reportes'))
        page = response.content.decode()
        self.assertLess(page.index('Atención clínica'), page.index('Operaciones'))
        self.assertLess(page.index('Operaciones'), page.index('Administración'))
        self.assertEqual(page.count('Ventas / POS'), 1)

        cashier = User.objects.create_user(
            username='navigation-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
            is_staff=True,
        )
        self.client.force_login(cashier)
        response = self.client.get(reverse('control:dashboard'))

        self.assertContains(response, 'Ventas / POS')
        self.assertContains(response, 'Pacientes')
        self.assertContains(response, 'Citas')
        self.assertNotContains(response, 'Gestión de usuarios')
        self.assertNotContains(response, 'Configuración')
        self.assertNotContains(response, 'Oftalmólogos')
        self.assertNotContains(response, 'Inventario')
        admin_response = self.client.get(reverse('admin:index'))
        self.assertEqual(admin_response.status_code, 302)

    def test_cashier_cannot_open_administrator_views_by_url(self):
        cashier = User.objects.create_user(
            username='url-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        self.client.force_login(cashier)

        for url_name in (
            'control:inventario_list',
            'control:oftalmologos_list',
            'control:inventario_export_csv',
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertRedirects(response, reverse('control:dashboard'))

        response = self.client.get(reverse('control:venta_create'))
        self.assertEqual(response.status_code, 200)

        patient = Paciente.objects.create(
            nombre='Paciente',
            apellido='Protegido',
            dni='12345678',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 25),
        )
        response = self.client.post(
            reverse('control:paciente_delete', args=[patient.pk]),
        )
        self.assertRedirects(response, reverse('control:dashboard'))
        self.assertTrue(Paciente.objects.filter(pk=patient.pk).exists())

    def test_administrator_can_permanently_delete_unreferenced_patient(self):
        admin = User.objects.create_user(
            username='patient-delete-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
        )
        patient = Paciente.objects.create(
            nombre='Paciente',
            apellido='Eliminable',
            dni='12345678',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 25),
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('control:paciente_delete', args=[patient.pk]),
        )

        self.assertRedirects(response, reverse('control:pacientes_list'))
        self.assertFalse(Paciente.objects.filter(pk=patient.pk).exists())

    def test_patient_delete_removes_clinical_and_sales_history_atomically(self):
        admin = User.objects.create_user(
            username='patient-cascade-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
        )
        patient = Paciente.objects.create(
            nombre='Paciente',
            apellido='Con historial',
            dni='12345678',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 25),
        )
        ophthalmologist = Oftalmologo.objects.create(
            nombre='Ana',
            apellido='Vega',
            dni='87654321',
            numero_colegiatura='PAT-CASCADE-1',
        )
        appointment = Cita.objects.create(
            paciente=patient,
            oftalmologo=ophthalmologist,
            fecha_hora=timezone.now(),
            motivo_consulta='Control visual',
        )
        consultation = ConsultaMedica.objects.create(
            cita=appointment,
            paciente=patient,
            oftalmologo=ophthalmologist,
            fecha_atencion=timezone.now(),
            sintomas='Visión borrosa',
            diagnostico='Miopía',
        )
        procedure = ProcedimientoOftalmologico.objects.create(
            consulta=consultation,
            tipo_intervencion='Procedimiento de prueba',
            ojo_intervenido=ProcedimientoOftalmologico.Ojo.DERECHO,
            fecha=timezone.localdate(),
        )
        prescription = RecetaOftalmologica.objects.create(
            consulta=consultation,
            paciente=patient,
            oftalmologo=ophthalmologist,
            esfera_od=Decimal('-1.00'),
            cilindro_od=Decimal('0.00'),
            eje_od=0,
            esfera_oi=Decimal('-1.00'),
            cilindro_oi=Decimal('0.00'),
            eje_oi=0,
        )
        category = Categoria.objects.create(nombre='PacienteCascade')
        product = Producto.objects.create(
            categoria=category,
            codigo_barras='PAT-CASCADE-PRODUCT',
            nombre='Producto de prueba',
            precio_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
        )
        sale = Venta.objects.create(
            paciente=patient,
            usuario=admin,
            receta=prescription,
            subtotal=Decimal('20.00'),
            total=Decimal('20.00'),
            metodo_pago=Venta.MetodoPago.EFECTIVO,
        )
        detail = DetalleVenta.objects.create(
            venta=sale,
            producto=product,
            cantidad=1,
            precio_unitario=Decimal('20.00'),
            subtotal=Decimal('20.00'),
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('control:paciente_delete', args=[patient.pk]),
        )

        self.assertRedirects(response, reverse('control:pacientes_list'))
        self.assertFalse(Paciente.objects.filter(pk=patient.pk).exists())
        self.assertFalse(Cita.objects.filter(pk=appointment.pk).exists())
        self.assertFalse(ConsultaMedica.objects.filter(pk=consultation.pk).exists())
        self.assertFalse(ProcedimientoOftalmologico.objects.filter(pk=procedure.pk).exists())
        self.assertFalse(RecetaOftalmologica.objects.filter(pk=prescription.pk).exists())
        self.assertFalse(Venta.objects.filter(pk=sale.pk).exists())
        self.assertFalse(DetalleVenta.objects.filter(pk=detail.pk).exists())
        self.assertTrue(Producto.objects.filter(pk=product.pk).exists())

    def test_role_admin_site_uses_optivision_brand(self):
        admin = User.objects.create_user(
            username='admin-site-user',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OptiVision')


class LoginBrandingTests(TestCase):
    def test_login_uses_optivision_logo_and_brand(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>OptiVision</title>')
        self.assertNotContains(response, '<title>Iniciar sesión')
        self.assertContains(response, 'brand/optivision-mark.svg')
        self.assertContains(response, 'viewBox="0 0 48 48"')
        self.assertContains(response, 'lg:grid-cols-2')
        self.assertContains(response, 'Ingresar al sistema')
        self.assertNotContains(response, 'arrow_forward')
        self.assertNotContains(response, 'arrow_back')


class StrictFormValidationTests(TestCase):
    def test_paciente_requires_eight_digit_dni_and_nine_digit_phone(self):
        data = {
            'nombre': 'Ana',
            'apellido': 'Pérez',
            'dni': '12345678\n',
            'fecha_nacimiento': '1990-01-01',
            'telefono': '987654321\n',
            'email': '',
            'direccion': '',
            'historial_medico_previo': '',
        }
        form = PacienteForm(data)

        self.assertFalse(form.is_valid())
        self.assertIn('dni', form.errors)
        self.assertIn('telefono', form.errors)

    def test_product_catalog_allows_a_default_image_placeholder(self):
        self.assertFalse(ProductoForm().fields['imagen'].required)

    def test_product_edit_without_upload_keeps_existing_image_reference(self):
        category = Categoria.objects.create(nombre='Accesorios')
        product = Producto.objects.create(
            categoria=category,
            codigo_barras='IMAGE-PRESERVE-1',
            nombre='Estuche óptico',
            precio_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
            imagen='productos/estuche.png',
        )
        form = ProductoForm(
            data={
                'categoria': str(category.pk),
                'subcategoria': '',
                'codigo_barras': product.codigo_barras,
                'nombre': 'Estuche actualizado',
                'marca': '',
                'modelo': '',
                'descripcion': '',
                'precio_compra': '10.00',
                'precio_venta': '20.00',
            },
            instance=product,
        )

        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.imagen.name, 'productos/estuche.png')

    def test_product_catalog_rejects_images_over_five_megabytes(self):
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), 'white').save(image_buffer, format='PNG')
        image_content = image_buffer.getvalue() + b'0' * (
            5 * 1024 * 1024 + 1
        )
        form = ProductoForm(
            data={
                'categoria': '',
                'subcategoria': '',
                'codigo_barras': 'LARGE-IMAGE',
                'nombre': 'Producto de prueba',
                'marca': '',
                'modelo': '',
                'descripcion': '',
                'precio_compra': '10.00',
                'precio_venta': '15.00',
            },
            files={
                'imagen': SimpleUploadedFile(
                    'producto.png',
                    image_content,
                    content_type='image/png',
                ),
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn('imagen', form.errors)


class AdministrationAndCashTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='operations-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
            is_staff=True,
        )

    def test_admin_can_create_users_and_save_system_parameters(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse('control:usuario_create'),
            {
                'username': 'newcashier',
                'first_name': 'Nuevo',
                'last_name': 'Cajero',
                'email': 'newcashier@example.test',
                'rol': User.Rol.CAJERO_VENDEDOR,
                'telefono': '987654321',
                'password1': 'SecureTestPass123!',
                'password2': 'SecureTestPass123!',
            },
        )
        self.assertRedirects(response, reverse('control:usuarios_list'))
        cashier = User.objects.get(username='newcashier')
        self.assertEqual(cashier.rol, User.Rol.CAJERO_VENDEDOR)
        self.assertTrue(cashier.check_password('SecureTestPass123!'))

        response = self.client.post(
            reverse('control:configuracion'),
            {
                'nombre_optica': 'OptiVision Pucallpa',
                'direccion': 'Jr. Ucayali',
                'telefono': '999888777',
                'ruc': '20123456789',
                'moneda': 'S/',
                'impuesto_porcentaje': '18.00',
            },
        )
        self.assertRedirects(response, reverse('control:configuracion'))
        self.assertEqual(
            ParametrosSistema.get_solo().nombre_optica,
            'OptiVision Pucallpa',
        )

    def test_admin_can_permanently_delete_user_account(self):
        cashier = User.objects.create_user(
            username='delete-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:usuario_delete', args=[cashier.pk]),
        )
        self.assertRedirects(response, reverse('control:usuarios_list'))
        self.assertFalse(User.objects.filter(pk=cashier.pk).exists())

    def test_user_delete_is_rejected_when_financial_records_reference_it(self):
        cashier = User.objects.create_user(
            username='cashier-protected',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        patient = Paciente.objects.create(
            nombre='Paciente',
            apellido='Compra',
            dni='87654322',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 25),
        )
        Venta.objects.create(
            paciente=patient,
            usuario=cashier,
            subtotal=Decimal('10.00'),
            total=Decimal('10.00'),
            metodo_pago=Venta.MetodoPago.EFECTIVO,
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:usuario_delete', args=[cashier.pk]),
        )

        self.assertRedirects(response, reverse('control:usuarios_list'))
        self.assertTrue(User.objects.filter(pk=cashier.pk).exists())

    def test_admin_cannot_delete_own_user_account(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:usuario_delete', args=[self.admin.pk]),
        )

        self.assertRedirects(response, reverse('control:usuarios_list'))
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_admin_can_open_product_inventory_and_reporting_screens(self):
        self.client.force_login(self.admin)
        for route_name in (
            'control:productos_list',
            'control:inventario_list',
            'control:reportes',
            'control:configuracion',
        ):
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))
                self.assertEqual(response.status_code, 200)
        dashboard = self.client.get(reverse('control:dashboard'))
        self.assertContains(dashboard, reverse('control:reportes'))
        self.assertContains(dashboard, reverse('control:configuracion'))

    def test_only_administrators_can_view_closed_cash_history(self):
        cashier = User.objects.create_user(
            username='history-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        ArqueoCaja.objects.create(
            usuario=cashier,
            monto_inicial=Decimal('50.00'),
            total_efectivo_ventas=Decimal('125.00'),
            total_tarjeta=Decimal('40.00'),
            total_transferencias=Decimal('12.00'),
            monto_cierre_real=Decimal('175.00'),
            diferencia=Decimal('0.00'),
            fecha_cierre=timezone.now(),
            estado=ArqueoCaja.Estado.CERRADA,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('control:arqueo_caja_historial'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'history-cashier')
        self.assertEqual(
            response.context['page_obj'][0].total_efectivo_ventas,
            Decimal('125.00'),
        )

        self.client.force_login(cashier)
        response = self.client.get(reverse('control:arqueo_caja_historial'))
        self.assertRedirects(response, reverse('control:dashboard'))

    def test_product_catalog_renders_svg_for_missing_product_image(self):
        category = Categoria.objects.create(nombre='Accesorios')
        Producto.objects.create(
            categoria=category,
            codigo_barras='PLACEHOLDER-1',
            nombre='Estuche óptico',
            precio_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse('control:productos_list'))

        self.assertContains(response, 'brand/product-placeholder.svg')
        self.assertNotContains(response, 'Imagen pendiente')

    def test_product_delete_is_rejected_when_sales_reference_it(self):
        category = Categoria.objects.create(nombre='Accesorios')
        product = Producto.objects.create(
            categoria=category,
            codigo_barras='ARCHIVE-1',
            nombre='Estuche',
            precio_compra=Decimal('10.00'),
            precio_venta=Decimal('20.00'),
        )
        patient = Paciente.objects.create(
            nombre='Paciente',
            apellido='Compra',
            dni='87654321',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 25),
        )
        sale = Venta.objects.create(
            paciente=patient,
            usuario=self.admin,
            subtotal=Decimal('20.00'),
            total=Decimal('20.00'),
            metodo_pago=Venta.MetodoPago.EFECTIVO,
        )
        DetalleVenta.objects.create(
            venta=sale,
            producto=product,
            cantidad=1,
            precio_unitario=Decimal('20.00'),
            subtotal=Decimal('20.00'),
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:producto_delete', args=[product.pk]),
        )

        self.assertRedirects(response, reverse('control:productos_list'))
        self.assertTrue(Producto.objects.filter(pk=product.pk).exists())

    def test_consultation_can_record_an_eye_procedure(self):
        patient = Paciente.objects.create(
            nombre='Lucía',
            apellido='Salas',
            dni='11223344',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 27),
        )
        ophthalmologist = Oftalmologo.objects.create(
            nombre='Ana',
            apellido='Vega',
            dni='44332211',
            numero_colegiatura='PROC-1001',
        )
        appointment = Cita.objects.create(
            paciente=patient,
            oftalmologo=ophthalmologist,
            fecha_hora=timezone.now(),
            motivo_consulta='Evaluación quirúrgica',
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:consulta_form', args=[appointment.pk]),
            {
                'sintomas': 'Visión opaca',
                'diagnostico': 'Catarata',
                'observaciones_clinicas': 'Evaluación completa.',
                'procedimientos-TOTAL_FORMS': '1',
                'procedimientos-INITIAL_FORMS': '0',
                'procedimientos-MIN_NUM_FORMS': '0',
                'procedimientos-MAX_NUM_FORMS': '10',
                'procedimientos-0-tipo_intervencion': 'Facoemulsificación',
                'procedimientos-0-ojo_intervenido': 'OD',
                'procedimientos-0-fecha': timezone.localdate().isoformat(),
                'procedimientos-0-observaciones': 'Sin complicaciones.',
            },
        )

        consultation = ConsultaMedica.objects.get(cita=appointment)
        self.assertRedirects(
            response,
            reverse('control:receta_form', args=[consultation.pk]),
        )
        procedure = ProcedimientoOftalmologico.objects.get(consulta=consultation)
        self.assertEqual(procedure.tipo_intervencion, 'Facoemulsificación')
        self.assertEqual(procedure.ojo_intervenido, 'OD')
        appointment.refresh_from_db()
        self.assertEqual(appointment.estado, Cita.Estado.ATENDIDA)

    def test_procedure_requires_type_eye_and_date_when_started(self):
        patient = Paciente.objects.create(
            nombre='Eva',
            apellido='Ríos',
            dni='55667788',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 31),
        )
        ophthalmologist = Oftalmologo.objects.create(
            nombre='Luis',
            apellido='Vega',
            dni='88776655',
            numero_colegiatura='PROC-1002',
        )
        appointment = Cita.objects.create(
            paciente=patient,
            oftalmologo=ophthalmologist,
            fecha_hora=timezone.now(),
            motivo_consulta='Control preoperatorio',
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('control:consulta_form', args=[appointment.pk]),
            {
                'sintomas': 'Molestia ocular',
                'diagnostico': 'En evaluación',
                'observaciones_clinicas': '',
                'procedimientos-TOTAL_FORMS': '1',
                'procedimientos-INITIAL_FORMS': '0',
                'procedimientos-MIN_NUM_FORMS': '0',
                'procedimientos-MAX_NUM_FORMS': '10',
                'procedimientos-0-tipo_intervencion': 'Cirugía',
                'procedimientos-0-ojo_intervenido': '',
                'procedimientos-0-fecha': '',
                'procedimientos-0-observaciones': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ConsultaMedica.objects.filter(cita=appointment).exists())
        self.assertContains(response, 'Completa este dato del procedimiento.')

    def test_pos_sale_is_linked_to_active_cash_shift_and_updates_payment_total(self):
        cashier = User.objects.create_user(
            username='cashier-pos',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        paciente = Paciente.objects.create(
            nombre='Elena',
            apellido='Vega',
            dni='87654321',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 30),
        )
        categoria = Categoria.objects.create(nombre='Monturas')
        producto = Producto.objects.create(
            categoria=categoria,
            codigo_barras='TEST-POS-1',
            nombre='Montura de prueba',
            precio_compra=Decimal('50.00'),
            precio_venta=Decimal('125.00'),
            stock_actual=4,
        )
        arqueo = ArqueoCaja.objects.create(
            usuario=cashier,
            monto_inicial=Decimal('100.00'),
        )
        self.client.force_login(cashier)

        response = self.client.post(
            reverse('control:venta_create'),
            {
                'venta-paciente': str(paciente.pk),
                'venta-receta': '',
                'venta-metodo_pago': Venta.MetodoPago.TARJETA,
                'items-TOTAL_FORMS': '1',
                'items-INITIAL_FORMS': '0',
                'items-MIN_NUM_FORMS': '1',
                'items-MAX_NUM_FORMS': '1000',
                'items-0-producto': str(producto.pk),
                'items-0-cantidad': '1',
            },
        )

        self.assertRedirects(response, reverse('control:ventas_list'))
        venta = Venta.objects.get(usuario=cashier)
        self.assertEqual(venta.arqueo, arqueo)
        self.assertEqual(venta.total, Decimal('125.00'))
        arqueo.refresh_from_db()
        self.assertEqual(arqueo.total_tarjeta, Decimal('125.00'))
        producto.refresh_from_db()
        self.assertEqual(producto.stock_actual, 3)

    def test_oftalmologo_uses_specialty_choices_and_strict_contact_validation(self):
        form = OftalmologoForm(
            data={
                'nombre': 'Ana',
                'apellido': 'Vega',
                'dni': '12345678',
                'numero_colegiatura': 'CMP-100',
                'especialidad': 'Especialidad inventada',
                'telefono': '123',
                'email': '',
                'horario_atencion': '',
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn('especialidad', form.errors)
        self.assertIn('telefono', form.errors)


class RecetasListTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='recetas-admin',
            password='test-password',
            rol=User.Rol.ADMINISTRADOR,
        )
        self.paciente = Paciente.objects.create(
            nombre='Rosa',
            apellido='Flores',
            dni='12345678',
            fecha_nacimiento=timezone.localdate() - timedelta(days=365 * 30),
        )
        self.oftalmologo = Oftalmologo.objects.create(
            nombre='Luis',
            apellido='Vega',
            dni='87654321',
            numero_colegiatura='CMP-REC-100',
        )
        cita = Cita.objects.create(
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            fecha_hora=timezone.now(),
            motivo_consulta='Control visual',
            estado=Cita.Estado.ATENDIDA,
        )
        consulta = ConsultaMedica.objects.create(
            cita=cita,
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            fecha_atencion=timezone.now(),
            sintomas='Visión borrosa',
            diagnostico='Miopía',
        )
        self.receta = RecetaOftalmologica.objects.create(
            consulta=consulta,
            paciente=self.paciente,
            oftalmologo=self.oftalmologo,
            esfera_od=Decimal('-1.00'),
            cilindro_od=Decimal('0.00'),
            eje_od=0,
            esfera_oi=Decimal('-1.00'),
            cilindro_oi=Decimal('0.00'),
            eje_oi=0,
        )

    def test_clinical_user_can_search_and_open_prescription(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('control:recetas_list'), {'q': '12345678'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rosa Flores')
        self.assertContains(
            response,
            reverse('control:receta_print', args=[self.receta.pk]),
        )

        response = self.client.get(
            reverse('control:receta_print', args=[self.receta.pk]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<title>OptiVision</title>')
        self.assertContains(response, 'brand/optivision-logo.svg')

    def test_clinical_user_can_download_prescription_pdf(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('control:receta_pdf', args=[self.receta.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn(b'%PDF', response.content)
        self.assertIn(
            f'receta-optivision-{self.receta.pk}.pdf',
            response['Content-Disposition'],
        )

    def test_cashier_cannot_view_prescriptions(self):
        cashier = User.objects.create_user(
            username='recetas-cashier',
            password='test-password',
            rol=User.Rol.CAJERO_VENDEDOR,
        )
        self.client.force_login(cashier)

        response = self.client.get(reverse('control:recetas_list'))

        self.assertRedirects(response, reverse('control:dashboard'))

    def test_patient_detail_groups_history_into_accessible_tabs(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse('control:paciente_detail', args=[self.paciente.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="tablist"')
        self.assertContains(response, 'Información personal')
        self.assertContains(response, 'Citas')
        self.assertContains(response, 'Consultas y procedimientos')
        self.assertContains(response, 'Recetas')


class SeedDataCommandTests(TestCase):
    def test_seed_data_creates_demo_records_once(self):
        call_command('seed_data', stdout=StringIO())
        call_command('seed_data', stdout=StringIO())

        admin = User.objects.get(username='admin')
        self.assertTrue(admin.check_password('admin123'))
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.rol, User.Rol.ADMINISTRADOR)
        cashier = User.objects.get(username='cajero1')
        self.assertTrue(cashier.check_password('cajero123'))
        self.assertEqual(
            Oftalmologo.objects.get(dni='87654321').especialidad,
            Oftalmologo.Especialidad.OPTOMETRIA,
        )
        self.assertEqual(cashier.rol, User.Rol.CAJERO_VENDEDOR)
        self.assertEqual(Paciente.objects.count(), 2)
        self.assertEqual(Oftalmologo.objects.count(), 2)
        self.assertTrue(
            Paciente.objects.filter(
                dni='23456789',
                telefono='976543210',
            ).exists(),
        )
        self.assertEqual(
            Oftalmologo.objects.get(dni='76543210').especialidad,
            Oftalmologo.Especialidad.GENERAL,
        )
        self.assertEqual(Producto.objects.count(), 10)
        self.assertEqual(
            Producto.objects.filter(descripcion='').count(),
            0,
        )
        self.assertEqual(
            Producto.objects.get(codigo_barras='OPT100000001').stock_actual,
            19,
        )
        self.assertEqual(
            set(
                Producto.objects.values_list('nombre', flat=True)
            ),
            {
                'Montura de acetato Ray-Ban',
                'Montura metálica minimalista',
                'Lunas antirreflejo Blue Protect',
                'Lunas bifocales orgánicas',
                'Lunas progresivas digitales',
                'Lentes de sol polarizados con medida',
                'Líquido limpiador de lunas 120 ml',
                'Estuche rígido de cuero para gafas',
                'Paño de microfibra antiempañante',
                'Lentes de descanso para computadora',
            },
        )
        self.assertEqual(DetalleVenta.objects.count(), 1)
        self.assertEqual(Venta.objects.filter(usuario=cashier).count(), 1)
        self.assertEqual(
            ArqueoCaja.objects.filter(
                usuario=cashier,
                fecha_apertura__date=timezone.localdate(),
            ).count(),
            1,
        )
        self.assertEqual(
            Cita.objects.filter(paciente__dni='12345678').count(),
            2,
        )
        self.assertTrue(
            Cita.objects.filter(
                paciente__dni='12345678',
                estado=Cita.Estado.PENDIENTE,
                fecha_hora__gt=timezone.now(),
            ).exists(),
        )
