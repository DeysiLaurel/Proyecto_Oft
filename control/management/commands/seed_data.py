from datetime import datetime, time, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from control.models import (
    ArqueoCaja,
    Categoria,
    Cita,
    ConsultaMedica,
    DetalleVenta,
    Oftalmologo,
    Paciente,
    Producto,
    RecetaOftalmologica,
    Subcategoria,
    User,
    Venta,
)


PRODUCTOS = (
    {
        'codigo_barras': 'OPT100000001',
        'nombre': 'Montura de acetato Ray-Ban',
        'marca': 'Ray-Ban',
        'modelo': 'RX5228 negro',
        'categoria': 'Lunas oftálmicas',
        'subcategoria': 'Antirreflejo',
        'descripcion': 'Armazón óptico de acetato negro de diseño rectangular, bisagras reforzadas y acabado pulido; indicado para uso diario.',
        'precio_compra': Decimal('210.00'),
        'precio_venta': Decimal('349.00'),
        'stock_actual': 20,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000002',
        'nombre': 'Montura metálica minimalista',
        'marca': 'OptiVision',
        'modelo': 'Titanium Air OV-02',
        'categoria': 'Monturas',
        'subcategoria': 'Metal',
        'descripcion': 'Armazón metálico ultraligero color plata, perfil minimalista, plaquetas nasales ajustables y terminales ergonómicos.',
        'precio_compra': Decimal('95.00'),
        'precio_venta': Decimal('189.00'),
        'stock_actual': 15,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000003',
        'nombre': 'Lunas antirreflejo Blue Protect',
        'marca': 'ClearView',
        'modelo': 'Blue Protect 1.56',
        'categoria': 'Monturas',
        'subcategoria': 'Acetato',
        'descripcion': 'Par de lunas orgánicas índice 1.56 con tratamiento antirreflejo multicapa y filtro de luz azul para pantallas.',
        'precio_compra': Decimal('65.00'),
        'precio_venta': Decimal('149.00'),
        'stock_actual': 20,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000004',
        'nombre': 'Lunas bifocales orgánicas',
        'marca': 'ClearView',
        'modelo': 'Bifocal FT-28',
        'categoria': 'Lunas oftálmicas',
        'subcategoria': 'Bifocales',
        'descripcion': 'Lunas bifocales orgánicas con segmento de lectura FT-28, superficie endurecida y protección UV para visión cercana y lejana.',
        'precio_compra': Decimal('68.00'),
        'precio_venta': Decimal('159.00'),
        'stock_actual': 15,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000005',
        'nombre': 'Lunas progresivas digitales',
        'marca': 'ClearView',
        'modelo': 'Digital Progressive 1.60',
        'categoria': 'Lunas oftálmicas',
        'subcategoria': 'Progresivas',
        'descripcion': 'Lunas progresivas digitales de diseño personalizado, transición gradual entre visión lejana, intermedia y cercana, índice 1.60.',
        'precio_compra': Decimal('185.00'),
        'precio_venta': Decimal('389.00'),
        'stock_actual': 15,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000006',
        'nombre': 'Lentes de sol polarizados con medida',
        'marca': 'Selva Sun',
        'modelo': 'Polarized RX SS-06',
        'categoria': 'Lentes de sol',
        'subcategoria': 'Polarizados',
        'descripcion': 'Lentes polarizados con protección UV400 y montura envolvente, preparados para adaptación de lunas oftálmicas graduadas.',
        'precio_compra': Decimal('110.00'),
        'precio_venta': Decimal('239.00'),
        'stock_actual': 20,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000007',
        'nombre': 'Líquido limpiador de lunas 120 ml',
        'marca': 'LensCare',
        'modelo': 'Cleaner Spray 120',
        'categoria': 'Accesorios y cuidado',
        'subcategoria': 'Limpieza',
        'descripcion': 'Solución limpiadora sin alcohol en atomizador de 120 ml, apta para lunas con recubrimiento antirreflejo.',
        'precio_compra': Decimal('9.00'),
        'precio_venta': Decimal('19.90'),
        'stock_actual': 20,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000008',
        'nombre': 'Estuche rígido de cuero para gafas',
        'marca': 'LensCare',
        'modelo': 'Leather Case LC-08',
        'categoria': 'Accesorios y cuidado',
        'subcategoria': 'Estuches',
        'descripcion': 'Estuche semirrígido forrado en cuero sintético con interior aterciopelado y cierre seguro para proteger las gafas de golpes y polvo.',
        'precio_compra': Decimal('18.00'),
        'precio_venta': Decimal('39.90'),
        'stock_actual': 15,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000009',
        'nombre': 'Paño de microfibra antiempañante',
        'marca': 'LensCare',
        'modelo': 'Anti-Fog Microfiber 18x15',
        'categoria': 'Accesorios y cuidado',
        'subcategoria': 'Limpieza',
        'descripcion': 'Paño de microfibra de 18 x 15 cm con tratamiento antiempañante reutilizable; limpia las lunas sin rayar sus recubrimientos.',
        'precio_compra': Decimal('6.00'),
        'precio_venta': Decimal('14.90'),
        'stock_actual': 20,
        'stock_minimo_alerta': 5,
    },
    {
        'codigo_barras': 'OPT100000010',
        'nombre': 'Lentes de descanso para computadora',
        'marca': 'OptiVision',
        'modelo': 'Computer Relax OV-10',
        'categoria': 'Accesorios y cuidado',
        'subcategoria': 'Lentes de descanso',
        'descripcion': 'Lentes de descanso con filtro de luz azul, montura liviana y lunas transparentes para comodidad durante el trabajo prolongado frente a pantallas.',
        'precio_compra': Decimal('45.00'),
        'precio_venta': Decimal('99.00'),
        'stock_actual': 15,
        'stock_minimo_alerta': 5,
    },
)


class Command(BaseCommand):
    help = 'Crea datos de demostración idempotentes para OptiVision.'

    @transaction.atomic
    def handle(self, *args, **options):
        admin, admin_created = self._get_user(
            'admin',
            'admin123',
            {
                'first_name': 'Administrador',
                'last_name': 'OptiVision',
                'email': 'admin@optivision.local',
                'rol': User.Rol.ADMINISTRADOR,
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        cashier, cashier_created = self._get_user(
            'cajero1',
            'cajero123',
            {
                'first_name': 'Cajero',
                'last_name': 'Demo',
                'email': 'cajero@optivision.local',
                'rol': User.Rol.CAJERO_VENDEDOR,
                'telefono': '999000001',
                'is_active': True,
            },
        )

        today = timezone.localdate()
        paciente, _ = Paciente.objects.update_or_create(
            dni='12345678',
            defaults={
                'nombre': 'María',
                'apellido': 'García',
                'fecha_nacimiento': today - timedelta(days=365 * 32),
                'telefono': '987654321',
                'email': 'maria.garcia@example.test',
                'direccion': 'Jr. Ucayali, Pucallpa',
                'historial_medico_previo': 'Sin antecedentes oftalmológicos relevantes.',
            },
        )
        Paciente.objects.update_or_create(
            dni='23456789',
            defaults={
                'nombre': 'Carlos',
                'apellido': 'Ríos',
                'fecha_nacimiento': today - timedelta(days=365 * 45),
                'telefono': '976543210',
                'email': 'carlos.rios@example.test',
                'direccion': 'Av. Amazonas, Pucallpa',
                'historial_medico_previo': 'Usa lentes para lectura.',
            },
        )
        oftalmologo, _ = Oftalmologo.objects.update_or_create(
            dni='87654321',
            defaults={
                'nombre': 'Lucía',
                'apellido': 'Ramírez',
                'numero_colegiatura': 'CMP-DEMO-001',
                'especialidad': Oftalmologo.Especialidad.OPTOMETRIA,
                'telefono': '988765432',
                'email': 'lucia.ramirez@optivision.local',
                'horario_atencion': 'Lunes a viernes, 09:00 a 17:00',
            },
        )
        Oftalmologo.objects.update_or_create(
            dni='76543210',
            defaults={
                'nombre': 'Jorge',
                'apellido': 'Salazar',
                'numero_colegiatura': 'CMP-DEMO-002',
                'especialidad': Oftalmologo.Especialidad.GENERAL,
                'telefono': '977654321',
                'email': 'jorge.salazar@optivision.local',
                'horario_atencion': 'Martes a sábado, 09:00 a 17:00',
            },
        )

        cita_pendiente = self._get_cita(
            paciente,
            oftalmologo,
            timezone.make_aware(
                datetime.combine(today + timedelta(days=1), time(9, 0)),
            ),
            'Control visual programado',
            Cita.Estado.PENDIENTE,
        )
        cita_atendida = self._get_cita(
            paciente,
            oftalmologo,
            timezone.make_aware(
                datetime.combine(today - timedelta(days=1), time(10, 0)),
            ),
            'Evaluación visual de demostración',
            Cita.Estado.ATENDIDA,
        )
        consulta, _ = ConsultaMedica.objects.get_or_create(
            cita=cita_atendida,
            defaults={
                'paciente': paciente,
                'oftalmologo': oftalmologo,
                'fecha_atencion': cita_atendida.fecha_hora,
                'sintomas': 'Visión borrosa ocasional de lejos.',
                'diagnostico': 'Miopía leve bilateral.',
                'observaciones_clinicas': 'Control anual recomendado.',
                'atendido_por': admin,
            },
        )
        if cita_atendida.estado != Cita.Estado.ATENDIDA:
            cita_atendida.estado = Cita.Estado.ATENDIDA
            cita_atendida.save(update_fields=['estado'])
        RecetaOftalmologica.objects.get_or_create(
            consulta=consulta,
            defaults={
                'paciente': paciente,
                'oftalmologo': oftalmologo,
                'esfera_od': Decimal('-1.00'),
                'cilindro_od': Decimal('-0.25'),
                'eje_od': 90,
                'esfera_oi': Decimal('-0.75'),
                'cilindro_oi': Decimal('-0.50'),
                'eje_oi': 85,
                'adicion': None,
                'distancia_pupilar': Decimal('63.00'),
                'tipo_lente_sugerido': 'Monofocal con antirreflejo',
            },
        )

        productos = []
        categorias = {}
        subcategorias = {}
        for item in PRODUCTOS:
            categoria = categorias.get(item['categoria'])
            if categoria is None:
                categoria, _ = Categoria.objects.get_or_create(
                    nombre=item['categoria'],
                    defaults={'descripcion': f"Productos de {item['categoria'].lower()}."},
                )
                categorias[item['categoria']] = categoria
            subcategoria = subcategorias.get((item['categoria'], item['subcategoria']))
            if subcategoria is None:
                subcategoria, _ = Subcategoria.objects.get_or_create(
                    categoria=categoria,
                    nombre=item['subcategoria'],
                )
                subcategorias[(item['categoria'], item['subcategoria'])] = subcategoria
            producto_defaults = {
                'categoria': categoria,
                'subcategoria': subcategoria,
                'nombre': item['nombre'],
                'marca': item['marca'],
                'modelo': item['modelo'],
                'descripcion': item['descripcion'],
                'precio_compra': item['precio_compra'],
                'precio_venta': item['precio_venta'],
                'stock_actual': item['stock_actual'],
                'stock_minimo_alerta': item['stock_minimo_alerta'],
                'creado_por': admin,
            }
            producto, producto_created = Producto.objects.get_or_create(
                codigo_barras=item['codigo_barras'],
                defaults=producto_defaults,
            )
            if not producto_created:
                updated_fields = []
                for field, value in producto_defaults.items():
                    if field == 'stock_actual':
                        continue
                    if getattr(producto, field) != value:
                        setattr(producto, field, value)
                        updated_fields.append(field)
                if updated_fields:
                    producto.save(update_fields=updated_fields)
            productos.append(producto)

        caja = ArqueoCaja.objects.filter(
            usuario=cashier,
            fecha_apertura__date=today,
            estado=ArqueoCaja.Estado.ABIERTA,
        ).first()
        caja_created = caja is None
        if caja_created:
            caja = ArqueoCaja.objects.create(
                usuario=cashier,
                estado=ArqueoCaja.Estado.ABIERTA,
                monto_inicial=Decimal('100.00'),
            )
        producto_venta = productos[0]
        venta = Venta.objects.filter(
            usuario=cashier,
            paciente=paciente,
            detalles__producto=producto_venta,
            estado=Venta.Estado.COMPLETADA,
        ).order_by('pk').first()
        venta_created = venta is None
        if venta_created:
            venta = Venta.objects.create(
                paciente=paciente,
                usuario=cashier,
                arqueo=caja,
                subtotal=producto_venta.precio_venta,
                total=producto_venta.precio_venta,
                metodo_pago=Venta.MetodoPago.EFECTIVO,
                estado=Venta.Estado.COMPLETADA,
            )
            DetalleVenta.objects.create(
                venta=venta,
                producto=producto_venta,
                cantidad=1,
                precio_unitario=producto_venta.precio_venta,
                subtotal=producto_venta.precio_venta,
            )
            Producto.objects.filter(pk=productos[0].pk).update(
                stock_actual=max(0, producto_venta.stock_actual - 1),
            )
        elif venta.arqueo_id is None:
            venta.arqueo = caja
            venta.save(update_fields=['arqueo'])

        caja_totales = Venta.objects.filter(
            arqueo=caja,
            estado=Venta.Estado.COMPLETADA,
        ).aggregate(
            efectivo=Sum(
                'total',
                filter=Q(metodo_pago=Venta.MetodoPago.EFECTIVO),
            ),
            tarjeta=Sum(
                'total',
                filter=Q(metodo_pago=Venta.MetodoPago.TARJETA),
            ),
            transferencias=Sum(
                'total',
                filter=Q(metodo_pago=Venta.MetodoPago.YAPE_PLIN),
            ),
        )
        caja.total_efectivo_ventas = caja_totales['efectivo'] or 0
        caja.total_tarjeta = caja_totales['tarjeta'] or 0
        caja.total_transferencias = caja_totales['transferencias'] or 0
        caja.save(
            update_fields=[
                'total_efectivo_ventas',
                'total_tarjeta',
                'total_transferencias',
            ],
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Datos demo listos: 2 usuarios, 2 pacientes, 2 oftalmólogos, '
                '2 citas, consulta, receta, 10 productos y una venta.',
            ),
        )
        if admin_created or cashier_created:
            self.stdout.write(
                'Credenciales de demostración: admin / admin123; '
                'cajero1 / cajero123.',
            )
        if caja_created:
            self.stdout.write('Se abrió una caja demo para cajero1.')
        if venta_created:
            self.stdout.write('Venta demo registrada.')

    @staticmethod
    def _get_user(username, password, defaults):
        user, created = User.objects.get_or_create(
            username=username,
            defaults=defaults,
        )
        if created:
            user.set_password(password)
            user.save(update_fields=['password'])
        else:
            changed_fields = []
            for field, value in defaults.items():
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    changed_fields.append(field)
            if changed_fields:
                user.save(update_fields=changed_fields)
        if not user.check_password(password):
            user.set_password(password)
            user.save(update_fields=['password'])
        return user, created

    @staticmethod
    def _get_cita(paciente, oftalmologo, fecha_hora, motivo, estado):
        cita = Cita.objects.filter(
            paciente=paciente,
            oftalmologo=oftalmologo,
            motivo_consulta=motivo,
        ).order_by('pk').first()
        if cita is None:
            cita = Cita.objects.create(
                paciente=paciente,
                oftalmologo=oftalmologo,
                fecha_hora=fecha_hora,
                motivo_consulta=motivo,
                estado=estado,
            )
        elif cita.fecha_hora != fecha_hora or cita.estado != estado:
            cita.fecha_hora = fecha_hora
            cita.estado = estado
            cita.save(update_fields=['fecha_hora', 'estado'])
        return cita
