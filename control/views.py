import csv
from io import BytesIO
from xml.sax.saxutils import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .forms import (
    ArqueoAperturaForm,
    ArqueoCierreForm,
    CategoriaForm,
    CitaForm,
    ConsultaMedicaForm,
    OftalmologoForm,
    PacienteForm,
    ParametrosSistemaForm,
    ProcedimientoFormSet,
    ProductoForm,
    ReportePeriodoForm,
    RecetaOftalmologicaForm,
    StockForm,
    SubcategoriaForm,
    UsuarioCreateForm,
    UsuarioUpdateForm,
    VentaForm,
    VentaItemFormSet,
)
from .decorators import (
    admin_required,
    cashier_or_admin_required,
    clinical_required,
)
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
    Subcategoria,
    User,
    Venta,
)


@login_required
def dashboard(request):
    today = timezone.localdate()
    ventas_hoy = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA,
        fecha_venta__date=today,
    ).aggregate(total=Sum('total'))['total'] or 0
    citas_hoy = Cita.objects.filter(
        fecha_hora__date=today,
    ).exclude(estado=Cita.Estado.CANCELADA)
    citas_pendientes_hoy = citas_hoy.filter(
        estado=Cita.Estado.PENDIENTE,
    ).count()
    cola_espera = citas_hoy.filter(
        estado=Cita.Estado.PENDIENTE,
    ).select_related(
        'paciente',
        'oftalmologo',
        'consulta_medica__receta_oftalmologica',
    ).order_by('fecha_hora')
    productos_criticos = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo_alerta'),
    ).count()
    pacientes_total = Paciente.objects.count()
    procedimientos_hoy = ProcedimientoOftalmologico.objects.filter(
        fecha=today,
    ).count()
    ultimas_ventas = Venta.objects.select_related(
        'paciente',
        'usuario',
    ).order_by('-fecha_venta')[:8]
    return render(
        request,
        'control/dashboard.html',
        {
            'ventas_hoy': ventas_hoy,
            'fecha_hoy': today,
            'pacientes_programados_hoy': citas_hoy.values(
                'paciente_id',
            ).distinct().count(),
            'citas_pendientes_hoy': citas_pendientes_hoy,
            'cola_espera': cola_espera,
            'productos_criticos': productos_criticos,
            'pacientes_total': pacientes_total,
            'ultimas_ventas': ultimas_ventas,
            'procedimientos_hoy': procedimientos_hoy,
        },
    )


@login_required
@admin_required
def oftalmologos_list(request):
    query = request.GET.get('q', '').strip()
    oftalmologos = Oftalmologo.objects.all()
    if query:
        oftalmologos = oftalmologos.filter(
            Q(nombre__icontains=query)
            | Q(apellido__icontains=query)
            | Q(dni__icontains=query)
            | Q(numero_colegiatura__icontains=query)
            | Q(especialidad__icontains=query)
        )
    page_obj = Paginator(oftalmologos, 15).get_page(request.GET.get('page'))
    return render(
        request,
        'control/oftalmologos_list.html',
        {'page_obj': page_obj, 'query': query},
    )


@login_required
@admin_required
def oftalmologo_create(request):
    form = OftalmologoForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        oftalmologo = form.save()
        messages.success(
            request,
            f'Oftalmólogo «{oftalmologo.nombre} {oftalmologo.apellido}» registrado.',
        )
        return redirect('control:oftalmologos_list')
    return render(
        request,
        'control/oftalmologo_form.html',
        {'form': form, 'titulo': 'Registrar oftalmólogo'},
    )


@login_required
@admin_required
def oftalmologo_update(request, pk):
    oftalmologo = get_object_or_404(Oftalmologo, pk=pk)
    form = OftalmologoForm(
        request.POST if request.method == 'POST' else None,
        instance=oftalmologo,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Los datos del oftalmólogo se actualizaron.')
        return redirect('control:oftalmologos_list')
    return render(
        request,
        'control/oftalmologo_form.html',
        {
            'form': form,
            'titulo': 'Editar oftalmólogo',
            'oftalmologo': oftalmologo,
        },
    )


@login_required
@admin_required
@require_POST
def oftalmologo_delete(request, pk):
    oftalmologo = get_object_or_404(Oftalmologo, pk=pk)
    try:
        oftalmologo.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar al oftalmólogo porque tiene citas o consultas asociadas.',
        )
    else:
        messages.success(request, 'El oftalmólogo se eliminó definitivamente.')
    return redirect('control:oftalmologos_list')


@login_required
@admin_required
def usuarios_list(request):
    query = request.GET.get('q', '').strip()
    usuarios = User.objects.order_by('username')
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )
    page_obj = Paginator(usuarios, 20).get_page(request.GET.get('page'))
    return render(
        request,
        'control/usuarios_list.html',
        {'page_obj': page_obj, 'query': query},
    )


@login_required
@admin_required
def usuario_create(request):
    form = UsuarioCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(
            request,
            f'Usuario «{usuario.username}» creado correctamente.',
        )
        return redirect('control:usuarios_list')
    return render(
        request,
        'control/usuario_form.html',
        {'form': form, 'titulo': 'Crear usuario'},
    )


@login_required
@admin_required
def usuario_update(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UsuarioUpdateForm(
        request.POST or None,
        instance=usuario,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request,
            f'Los datos de «{usuario.username}» fueron actualizados.',
        )
        return redirect('control:usuarios_list')
    return render(
        request,
        'control/usuario_form.html',
        {'form': form, 'titulo': 'Editar usuario', 'usuario': usuario},
    )


@login_required
@admin_required
@require_POST
def usuario_delete(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, 'No puedes eliminar tu propia cuenta.')
        return redirect('control:usuarios_list')
    if (
        usuario.is_active
        and usuario.rol == User.Rol.ADMINISTRADOR
        and User.objects.filter(
            is_active=True,
            rol=User.Rol.ADMINISTRADOR,
        ).count() <= 1
    ):
        messages.error(request, 'No puedes eliminar al último administrador activo.')
        return redirect('control:usuarios_list')
    try:
        usuario.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar esta cuenta porque tiene ventas o arqueos asociados.',
        )
    else:
        messages.success(request, 'La cuenta se eliminó definitivamente.')
    return redirect('control:usuarios_list')


@login_required
@admin_required
def configuracion(request):
    parametros = ParametrosSistema.get_solo()
    form = ParametrosSistemaForm(
        request.POST or None,
        instance=parametros,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'La configuración se guardó correctamente.')
        return redirect('control:configuracion')
    return render(
        request,
        'control/configuracion.html',
        {'form': form},
    )


@login_required
def pacientes_list(request):
    query = request.GET.get('q', '').strip()
    pacientes = Paciente.objects.all()
    if query:
        pacientes = pacientes.filter(
            Q(nombre__icontains=query)
            | Q(apellido__icontains=query)
            | Q(dni__icontains=query)
        )
    page_obj = Paginator(pacientes, 15).get_page(request.GET.get('page'))
    return render(
        request,
        'control/pacientes_list.html',
        {'page_obj': page_obj, 'query': query},
    )


@login_required
@clinical_required
def paciente_detail(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    citas = paciente.citas.select_related('oftalmologo').order_by('-fecha_hora')
    consultas = paciente.consultas_medicas.select_related(
        'cita',
        'oftalmologo',
    ).prefetch_related('procedimientos').order_by('-fecha_atencion')
    recetas = paciente.recetas_oftalmologicas.select_related(
        'oftalmologo',
        'consulta',
    ).order_by('-fecha_emision')
    recetas_por_consulta = {receta.consulta_id: receta for receta in recetas}
    return render(
        request,
        'control/paciente_detail.html',
        {
            'paciente': paciente,
            'citas': citas,
            'recetas': recetas,
            'historial_consultas': [
                (consulta, recetas_por_consulta.get(consulta.pk))
                for consulta in consultas
            ],
        },
    )


@login_required
@clinical_required
def paciente_create(request):
    form = PacienteForm(
        request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        paciente = form.save()
        messages.success(request, 'El paciente se registró correctamente.')
        return redirect('control:paciente_detail', pk=paciente.pk)
    return render(
        request,
        'control/paciente_form.html',
        {'form': form, 'titulo': 'Registrar paciente'},
    )


@login_required
@clinical_required
def paciente_update(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk)
    form = PacienteForm(
        request.POST if request.method == 'POST' else None,
        instance=paciente,
    )
    if request.method == 'POST' and form.is_valid():
        paciente = form.save()
        messages.success(request, 'Los datos del paciente se actualizaron.')
        return redirect('control:paciente_detail', pk=paciente.pk)
    return render(
        request,
        'control/paciente_form.html',
        {
            'form': form,
            'titulo': 'Editar paciente',
            'paciente': paciente,
        },
    )


@login_required
@admin_required
@require_POST
def paciente_delete(request, pk):
    with transaction.atomic():
        paciente = get_object_or_404(
            Paciente.objects.select_for_update(),
            pk=pk,
        )
        consultas = ConsultaMedica.objects.filter(paciente=paciente)
        RecetaOftalmologica.objects.filter(
            Q(paciente=paciente) | Q(consulta_id__in=consultas.values('pk')),
        ).delete()
        consultas.delete()
        Cita.objects.filter(paciente=paciente).delete()
        Venta.objects.filter(paciente=paciente).delete()
        paciente.delete()
    messages.success(
        request,
        'El paciente y su historial clínico y comercial se eliminaron definitivamente.',
    )
    return redirect('control:pacientes_list')


@login_required
def citas_list(request):
    estado = request.GET.get('estado', '')
    citas = Cita.objects.select_related(
        'paciente',
        'oftalmologo',
    ).order_by('-fecha_hora')
    if estado in Cita.Estado.values:
        citas = citas.filter(estado=estado)
    page_obj = Paginator(citas, 15).get_page(request.GET.get('page'))
    return render(
        request,
        'control/citas_list.html',
        {
            'page_obj': page_obj,
            'estado_seleccionado': estado,
            'estados': Cita.Estado.choices,
        },
    )


@login_required
def cita_create(request):
    form = CitaForm(request.POST if request.method == 'POST' else None)
    paciente_id = request.GET.get('paciente')
    if request.method == 'GET' and paciente_id:
        form.initial['paciente'] = paciente_id
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'La cita se agendó correctamente.')
        return redirect('control:citas_list')
    return render(
        request,
        'control/cita_form.html',
        {
            'form': form,
            'titulo': 'Agendar cita',
            'pacientes_activos': form.fields['paciente'].queryset.exists(),
            'oftalmologos_activos': form.fields['oftalmologo'].queryset.exists(),
        },
    )


@login_required
@clinical_required
def consulta_form(request, cita_pk):
    cita = get_object_or_404(
        Cita.objects.select_related('paciente', 'oftalmologo'),
        pk=cita_pk,
    )
    if cita.estado == Cita.Estado.CANCELADA:
        messages.error(request, 'No se puede registrar una consulta para una cita cancelada.')
        return redirect('control:citas_list')

    consulta = ConsultaMedica.objects.filter(cita=cita).first()
    form = ConsultaMedicaForm(
        request.POST if request.method == 'POST' else None,
        instance=consulta,
    )
    procedimientos_formset = ProcedimientoFormSet(
        request.POST if request.method == 'POST' else None,
        instance=consulta or ConsultaMedica(),
        prefix='procedimientos',
    )
    if (
        request.method == 'POST'
        and form.is_valid()
        and procedimientos_formset.is_valid()
    ):
        with transaction.atomic():
            cita = get_object_or_404(
                Cita.objects.select_for_update().select_related(
                    'paciente',
                    'oftalmologo',
                ),
                pk=cita_pk,
            )
            if cita.estado == Cita.Estado.CANCELADA:
                messages.error(
                    request,
                    'La cita fue cancelada y no puede atenderse.',
                )
                return redirect('control:citas_list')
            consulta = ConsultaMedica.objects.filter(cita=cita).first()
            form.instance = consulta or form.instance
            consulta = form.save(commit=False)
            consulta.cita = cita
            consulta.paciente = cita.paciente
            consulta.oftalmologo = cita.oftalmologo
            consulta.atendido_por = request.user
            if not consulta.pk:
                consulta.fecha_atencion = timezone.now()
            consulta.save()
            procedimientos_formset.instance = consulta
            procedimientos_formset.save()
            if cita.estado != Cita.Estado.ATENDIDA:
                cita.estado = Cita.Estado.ATENDIDA
                cita.save(update_fields=['estado'])
        messages.success(
            request,
            'Consulta guardada. Puedes registrar o actualizar la receta oftalmológica.',
        )
        return redirect('control:receta_form', consulta_pk=consulta.pk)

    return render(
        request,
        'control/consulta_form.html',
        {
            'form': form,
            'cita': cita,
            'consulta': consulta,
            'procedimientos_formset': procedimientos_formset,
        },
    )


@login_required
@clinical_required
def receta_form(request, consulta_pk):
    consulta = get_object_or_404(
        ConsultaMedica.objects.select_related(
            'cita',
            'paciente',
            'oftalmologo',
        ),
        pk=consulta_pk,
    )
    receta = RecetaOftalmologica.objects.filter(consulta=consulta).first()
    form = RecetaOftalmologicaForm(
        request.POST if request.method == 'POST' else None,
        instance=receta,
    )
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            consulta = get_object_or_404(
                ConsultaMedica.objects.select_for_update().select_related(
                    'paciente',
                    'oftalmologo',
                ),
                pk=consulta_pk,
            )
            receta = RecetaOftalmologica.objects.filter(
                consulta=consulta,
            ).first()
            form.instance = receta or form.instance
            receta = form.save(commit=False)
            receta.consulta = consulta
            receta.paciente = consulta.paciente
            receta.oftalmologo = consulta.oftalmologo
            receta.save()
        messages.success(request, 'La receta oftalmológica se guardó correctamente.')
        return redirect('control:receta_print', receta_pk=receta.pk)
    return render(
        request,
        'control/receta_form.html',
        {'form': form, 'consulta': consulta, 'receta': receta},
    )


@login_required
@clinical_required
def receta_print(request, receta_pk):
    receta = get_object_or_404(
        RecetaOftalmologica.objects.select_related(
            'consulta',
            'paciente',
            'oftalmologo',
        ),
        pk=receta_pk,
    )
    return render(request, 'control/receta_print.html', {'receta': receta})


@login_required
@clinical_required
def receta_pdf(request, receta_pk):
    receta = get_object_or_404(
        RecetaOftalmologica.objects.select_related(
            'consulta',
            'paciente',
            'oftalmologo',
        ),
        pk=receta_pk,
    )
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f'Receta oftalmológica OptiVision #{receta.pk}',
        author='OptiVision',
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Brand',
        parent=styles['Title'],
        textColor=colors.HexColor('#003c90'),
        alignment=TA_CENTER,
        fontSize=20,
        leading=24,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        textColor=colors.HexColor('#003c90'),
        fontSize=12,
        leading=15,
        spaceBefore=14,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name='Cell',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12,
    ))

    def cell(value):
        return Paragraph(escape(str(value)), styles['Cell'])

    elements = [
        Paragraph('OptiVision', styles['Brand']),
        Paragraph(
            'CENTRO DE SALUD VISUAL · RECETA OFTALMOLÓGICA',
            styles['Normal'],
        ),
        Spacer(1, 8),
        Paragraph(
            f'Fecha de emisión: {receta.fecha_emision:%d/%m/%Y}',
            styles['Normal'],
        ),
        Paragraph('Datos del paciente', styles['SectionHeading']),
    ]
    patient_table = Table(
        [
            [cell('Paciente'), cell(
                f'{receta.paciente.nombre} {receta.paciente.apellido}',
            ), cell('DNI'), cell(receta.paciente.dni)],
            [cell('Oftalmólogo'), cell(
                f'{receta.oftalmologo.nombre} {receta.oftalmologo.apellido}',
            ), cell('CMP/COP'), cell(receta.oftalmologo.numero_colegiatura)],
            [cell('Fecha de consulta'), cell(
                receta.consulta.fecha_atencion.strftime('%d/%m/%Y'),
            ), cell('Especialidad'), cell(receta.oftalmologo.especialidad)],
        ],
        colWidths=[30 * mm, 60 * mm, 25 * mm, 45 * mm],
    )
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#eff6ff')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#eff6ff')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#003c90')),
        ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#003c90')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.extend([
        patient_table,
        Paragraph('Graduación', styles['SectionHeading']),
    ])
    prescription_table = Table(
        [
            [cell('Ojo'), cell('Esfera'), cell('Cilindro'), cell('Eje')],
            [
                cell('OD · Derecho'),
                cell(receta.esfera_od),
                cell(receta.cilindro_od),
                cell(f'{receta.eje_od}°'),
            ],
            [
                cell('OI · Izquierdo'),
                cell(receta.esfera_oi),
                cell(receta.cilindro_oi),
                cell(f'{receta.eje_oi}°'),
            ],
        ],
        colWidths=[55 * mm, 35 * mm, 35 * mm, 35 * mm],
    )
    prescription_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003c90')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
    ]))
    elements.extend([
        prescription_table,
        Paragraph('Indicaciones ópticas', styles['SectionHeading']),
        cell(
            'Adición: '
            f'{receta.adicion if receta.adicion is not None else "—"}'
            ' · Distancia pupilar: '
            f'{receta.distancia_pupilar if receta.distancia_pupilar is not None else "—"}'
            ' mm'
        ),
        Spacer(1, 8),
        cell(
            'Tipo de lente sugerido: '
            f'{receta.tipo_lente_sugerido or "—"}'
        ),
        Spacer(1, 45),
        cell(
            f'{receta.oftalmologo.nombre} {receta.oftalmologo.apellido}'
            f' · {receta.oftalmologo.numero_colegiatura}'
        ),
    ])
    document.build(elements)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="receta-optivision-{receta.pk}.pdf"'
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response


@login_required
@clinical_required
def recetas_list(request):
    query = request.GET.get('q', '').strip()
    recetas = RecetaOftalmologica.objects.select_related(
        'paciente',
        'oftalmologo',
        'consulta',
    ).order_by('-fecha_emision', '-pk')
    if query:
        recetas = recetas.filter(
            Q(paciente__nombre__icontains=query)
            | Q(paciente__apellido__icontains=query)
            | Q(paciente__dni__icontains=query)
            | Q(oftalmologo__nombre__icontains=query)
            | Q(oftalmologo__apellido__icontains=query)
        )
    page_obj = Paginator(recetas, 20).get_page(request.GET.get('page'))
    return render(
        request,
        'control/recetas_list.html',
        {'page_obj': page_obj, 'query': query},
    )


@login_required
@admin_required
def productos_list(request):
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related(
        'categoria',
        'subcategoria',
    ).order_by('nombre')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query)
            | Q(codigo_barras__icontains=query)
            | Q(marca__icontains=query)
        )
    page_obj = Paginator(productos, 20).get_page(request.GET.get('page'))
    return render(
        request,
        'control/productos_list.html',
        {
            'page_obj': page_obj,
            'query': query,
            'categorias': Categoria.objects.prefetch_related(
                'subcategorias',
            ),
            'categoria_form': CategoriaForm(),
            'subcategoria_form': SubcategoriaForm(),
        },
    )


@login_required
@admin_required
def inventario_list(request):
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.select_related('categoria').annotate(
        valor_stock=ExpressionWrapper(
            F('precio_compra') * F('stock_actual'),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    ).order_by('nombre')
    if query:
        productos = productos.filter(
            Q(nombre__icontains=query)
            | Q(codigo_barras__icontains=query)
            | Q(marca__icontains=query)
        )
    page_obj = Paginator(productos, 25).get_page(request.GET.get('page'))
    valor_inventario = Producto.objects.aggregate(
        valor=Sum(
            ExpressionWrapper(
                F('precio_compra') * F('stock_actual'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        ),
    )['valor'] or 0
    return render(
        request,
        'control/inventario_list.html',
        {
            'page_obj': page_obj,
            'query': query,
            'valor_inventario': valor_inventario,
            'productos_criticos': Producto.objects.filter(
                stock_actual__lte=F('stock_minimo_alerta'),
            ).count(),
        },
    )


@login_required
@admin_required
@require_POST
def inventario_update_stock(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = StockForm(request.POST, instance=producto)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f'Existencias de «{producto.nombre}» actualizadas.',
        )
    else:
        messages.error(request, 'Revisa las cantidades de stock ingresadas.')
    return redirect('control:inventario_list')


@login_required
@admin_required
def producto_create(request):
    form = ProductoForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
    )
    if request.method == 'POST' and form.is_valid():
        producto = form.save(commit=False)
        producto.creado_por = request.user
        producto.save()
        messages.success(request, f'Producto «{producto.nombre}» registrado.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/producto_form.html',
        {'form': form, 'titulo': 'Registrar producto'},
    )


@login_required
@admin_required
def producto_update(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(
        request.POST if request.method == 'POST' else None,
        request.FILES if request.method == 'POST' else None,
        instance=producto,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Los datos del producto se actualizaron.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/producto_form.html',
        {'form': form, 'titulo': 'Editar producto', 'producto': producto},
    )


@login_required
@admin_required
@require_POST
def producto_delete(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    imagen = producto.imagen
    try:
        producto.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar este producto porque forma parte de ventas registradas.',
        )
        return redirect('control:productos_list')
    if imagen:
        imagen.delete(save=False)
    messages.success(request, 'El producto se eliminó definitivamente.')
    return redirect('control:productos_list')


@login_required
@admin_required
def categoria_create(request):
    form = CategoriaForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoría creada correctamente.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/productos_list.html',
        {
            'page_obj': Paginator(
                Producto.objects.select_related('categoria', 'subcategoria'),
                20,
            ).get_page(request.GET.get('page')),
            'query': '',
            'categorias': Categoria.objects.prefetch_related('subcategorias'),
            'categoria_form': form,
            'subcategoria_form': SubcategoriaForm(),
        },
    )


@login_required
@admin_required
def subcategoria_create(request):
    form = SubcategoriaForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subcategoría creada correctamente.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/productos_list.html',
        {
            'page_obj': Paginator(
                Producto.objects.select_related('categoria', 'subcategoria'),
                20,
            ).get_page(request.GET.get('page')),
            'query': '',
            'categorias': Categoria.objects.prefetch_related('subcategorias'),
            'categoria_form': CategoriaForm(),
            'subcategoria_form': form,
        },
    )


@login_required
@admin_required
def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(
        request.POST if request.method == 'POST' else None,
        instance=categoria,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoría actualizada correctamente.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/catalog_form.html',
        {'form': form, 'titulo': 'Editar categoría'},
    )


@login_required
@admin_required
def subcategoria_update(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    form = SubcategoriaForm(
        request.POST if request.method == 'POST' else None,
        instance=subcategoria,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Subcategoría actualizada correctamente.')
        return redirect('control:productos_list')
    return render(
        request,
        'control/catalog_form.html',
        {'form': form, 'titulo': 'Editar subcategoría'},
    )


@login_required
@admin_required
@require_POST
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    try:
        categoria.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar esta categoría porque tiene productos asociados.',
        )
    else:
        messages.success(request, 'Categoría eliminada correctamente.')
    return redirect('control:productos_list')


@login_required
@admin_required
@require_POST
def subcategoria_delete(request, pk):
    subcategoria = get_object_or_404(Subcategoria, pk=pk)
    try:
        subcategoria.delete()
    except ProtectedError:
        messages.error(
            request,
            'No se puede eliminar esta subcategoría porque tiene productos asociados.',
        )
    else:
        messages.success(request, 'Subcategoría eliminada correctamente.')
    return redirect('control:productos_list')


@login_required
@cashier_or_admin_required
def ventas_list(request):
    ventas = Venta.objects.select_related(
        'paciente',
        'usuario',
    ).prefetch_related(
        'detalles__producto',
    )
    page_obj = Paginator(ventas, 20).get_page(request.GET.get('page'))
    return render(request, 'control/ventas_list.html', {'page_obj': page_obj})


@login_required
@cashier_or_admin_required
def venta_create(request):
    arqueo_activo = ArqueoCaja.objects.filter(
        usuario=request.user,
        estado=ArqueoCaja.Estado.ABIERTA,
    ).first()
    venta_form = VentaForm(
        request.POST if request.method == 'POST' else None,
        prefix='venta',
    )
    item_formset = VentaItemFormSet(
        request.POST if request.method == 'POST' else None,
        prefix='items',
    )

    if request.method == 'POST' and venta_form.is_valid() and item_formset.is_valid():
        items = [
            form.cleaned_data
            for form in item_formset.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        if not items:
            messages.error(request, 'Agrega al menos un producto a la venta.')
            return render(
                request,
                'control/venta_form.html',
                {
                    'venta_form': venta_form,
                    'item_formset': item_formset,
                    'arqueo_activo': arqueo_activo,
                    'precios_productos': {
                        str(product.pk): str(product.precio_venta)
                        for product in Producto.objects.all()
                    },
                },
            )

        product_ids = [item['producto'].pk for item in items]
        arqueo_activo = None
        with transaction.atomic():
            arqueo_activo = ArqueoCaja.objects.select_for_update().filter(
                usuario=request.user,
                estado=ArqueoCaja.Estado.ABIERTA,
            ).first()
            if arqueo_activo is None:
                messages.error(
                    request,
                    'Abre un turno de caja antes de registrar una venta.',
                )
                return redirect('control:arqueo_caja')
            locked_products = {
                product.pk: product
                for product in Producto.objects.select_for_update()
                .filter(pk__in=product_ids)
                .order_by('pk')
            }
            valid_stock = True
            for form in item_formset.forms:
                if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                    continue
                product_id = form.cleaned_data['producto'].pk
                product = locked_products.get(product_id)
                if product is None:
                    form.add_error('producto', 'El producto ya no está disponible.')
                    valid_stock = False
                elif product.stock_actual < form.cleaned_data['cantidad']:
                    form.add_error(
                        'cantidad',
                        f'Stock disponible: {product.stock_actual}.',
                    )
                    valid_stock = False

            if valid_stock:
                total = sum(
                    (
                        locked_products[item['producto'].pk].precio_venta
                        * item['cantidad']
                        for item in items
                    ),
                    start=0,
                )
                venta = venta_form.save(commit=False)
                venta.usuario = request.user
                venta.arqueo = arqueo_activo
                venta.subtotal = total
                venta.total = total
                venta.save()
                for item in items:
                    producto = locked_products[item['producto'].pk]
                    cantidad = item['cantidad']
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio_venta,
                        subtotal=producto.precio_venta * cantidad,
                    )
                    producto.stock_actual -= cantidad
                    producto.save(update_fields=['stock_actual'])
                total_por_pago = {
                    Venta.MetodoPago.EFECTIVO: 'total_efectivo_ventas',
                    Venta.MetodoPago.TARJETA: 'total_tarjeta',
                    Venta.MetodoPago.YAPE_PLIN: 'total_transferencias',
                }
                total_field = total_por_pago[venta.metodo_pago]
                setattr(
                    arqueo_activo,
                    total_field,
                    getattr(arqueo_activo, total_field) + total,
                )
                arqueo_activo.save(update_fields=[total_field])
        if valid_stock:
            messages.success(request, f'Venta #{venta.pk} registrada correctamente.')
            return redirect('control:ventas_list')

    return render(
        request,
        'control/venta_form.html',
        {
            'venta_form': venta_form,
            'item_formset': item_formset,
            'arqueo_activo': arqueo_activo,
        },
    )


@login_required
@cashier_or_admin_required
def arqueo_caja(request):
    arqueo_abierto = ArqueoCaja.objects.filter(
        usuario=request.user,
        estado=ArqueoCaja.Estado.ABIERTA,
    ).first()
    apertura_form = ArqueoAperturaForm(
        request.POST if request.method == 'POST' else None,
    )
    if request.method == 'POST' and apertura_form.is_valid():
        with transaction.atomic():
            User.objects.select_for_update().get(pk=request.user.pk)
            arqueo_abierto = ArqueoCaja.objects.filter(
                usuario=request.user,
                estado=ArqueoCaja.Estado.ABIERTA,
            ).first()
            if arqueo_abierto:
                messages.error(request, 'Ya tienes un turno de caja abierto.')
            else:
                arqueo_abierto = apertura_form.save(commit=False)
                arqueo_abierto.usuario = request.user
                arqueo_abierto.save()
                messages.success(request, 'La caja se abrió correctamente.')
                return redirect('control:arqueo_caja')

    contexto = {
        'arqueo': arqueo_abierto,
        'ultimo_arqueo': ArqueoCaja.objects.filter(
            usuario=request.user,
            estado=ArqueoCaja.Estado.CERRADA,
        ).first(),
        'apertura_form': apertura_form,
        'cierre_form': ArqueoCierreForm(),
    }
    if contexto['ultimo_arqueo']:
        contexto['ultimo_efectivo_esperado'] = (
            contexto['ultimo_arqueo'].monto_inicial
            + contexto['ultimo_arqueo'].total_efectivo_ventas
        )
    if arqueo_abierto:
        totales = Venta.objects.filter(
            usuario=request.user,
            estado=Venta.Estado.COMPLETADA,
            fecha_venta__gte=arqueo_abierto.fecha_apertura,
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
        contexto.update(
            {
                'total_efectivo': totales['efectivo'] or 0,
                'total_tarjeta': totales['tarjeta'] or 0,
                'total_transferencias': totales['transferencias'] or 0,
            },
        )
    return render(request, 'control/arqueo_caja.html', contexto)


@login_required
@admin_required
def arqueo_caja_historial(request):
    arqueos = ArqueoCaja.objects.filter(
        estado=ArqueoCaja.Estado.CERRADA,
    ).select_related('usuario').order_by('-fecha_cierre', '-pk')
    page_obj = Paginator(arqueos, 25).get_page(request.GET.get('page'))
    return render(
        request,
        'control/arqueo_caja_historial.html',
        {'page_obj': page_obj},
    )


@login_required
@cashier_or_admin_required
@require_POST
def arqueo_caja_cerrar(request, pk):
    cierre_form = ArqueoCierreForm(request.POST)
    if not cierre_form.is_valid():
        messages.error(request, 'Ingresa un monto válido para cerrar la caja.')
        return redirect('control:arqueo_caja')

    with transaction.atomic():
        arqueo = get_object_or_404(
            ArqueoCaja.objects.select_for_update(),
            pk=pk,
            usuario=request.user,
            estado=ArqueoCaja.Estado.ABIERTA,
        )
        ahora = timezone.now()
        totales = Venta.objects.filter(
            usuario=request.user,
            estado=Venta.Estado.COMPLETADA,
            fecha_venta__gte=arqueo.fecha_apertura,
            fecha_venta__lte=ahora,
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
        efectivo = totales['efectivo'] or 0
        tarjeta = totales['tarjeta'] or 0
        transferencias = totales['transferencias'] or 0
        esperado = arqueo.monto_inicial + efectivo
        arqueo.total_efectivo_ventas = efectivo
        arqueo.total_tarjeta = tarjeta
        arqueo.total_transferencias = transferencias
        arqueo.monto_cierre_real = cierre_form.cleaned_data['monto_cierre_real']
        arqueo.diferencia = arqueo.monto_cierre_real - esperado
        arqueo.fecha_cierre = ahora
        arqueo.estado = ArqueoCaja.Estado.CERRADA
        arqueo.save(
            update_fields=[
                'total_efectivo_ventas',
                'total_tarjeta',
                'total_transferencias',
                'monto_cierre_real',
                'diferencia',
                'fecha_cierre',
                'estado',
            ],
        )
    messages.success(request, 'La caja se cerró y el arqueo quedó registrado.')
    return redirect('control:arqueo_caja')


@login_required
@admin_required
def reportes(request):
    today = timezone.localdate()
    initial = {'desde': today.replace(day=1), 'hasta': today}
    form = ReportePeriodoForm(request.GET or None, initial=initial)
    if form.is_valid():
        desde = form.cleaned_data.get('desde') or initial['desde']
        hasta = form.cleaned_data.get('hasta') or today
    else:
        desde, hasta = initial['desde'], today

    ventas = Venta.objects.filter(
        estado=Venta.Estado.COMPLETADA,
        fecha_venta__date__gte=desde,
        fecha_venta__date__lte=hasta,
    )
    ingresos = ventas.aggregate(total=Sum('total'))['total'] or 0
    pagos = {
        row['metodo_pago']: row['total']
        for row in ventas.values('metodo_pago').annotate(total=Sum('total'))
    }
    ventas_por_cajero = ventas.values(
        'usuario__username',
        'usuario__first_name',
        'usuario__last_name',
    ).annotate(
        cantidad=Count('pk'),
        total=Sum('total'),
    ).order_by('-total')
    consultas = ConsultaMedica.objects.filter(
        fecha_atencion__date__gte=desde,
        fecha_atencion__date__lte=hasta,
    )
    valor_inventario = Producto.objects.aggregate(
        valor=Sum(
            ExpressionWrapper(
                F('precio_compra') * F('stock_actual'),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        ),
    )['valor'] or 0
    inventario_critico = Producto.objects.filter(
        stock_actual__lte=F('stock_minimo_alerta'),
    ).select_related('categoria').order_by('stock_actual', 'nombre')
    contexto = {
        'form': form,
        'desde': desde,
        'hasta': hasta,
        'ingresos': ingresos,
        'pagos': [
            {
                'nombre': label,
                'total': pagos.get(value, 0),
            }
            for value, label in Venta.MetodoPago.choices
        ],
        'ventas_por_cajero': ventas_por_cajero,
        'cantidad_ventas': ventas.count(),
        'cantidad_consultas': consultas.count(),
        'cantidad_recetas': RecetaOftalmologica.objects.filter(
            fecha_emision__gte=desde,
            fecha_emision__lte=hasta,
        ).count(),
        'pacientes_atendidos': consultas.values('paciente_id').distinct().count(),
        'valor_inventario': valor_inventario,
        'inventario_critico': inventario_critico,
    }
    return render(request, 'control/reportes.html', contexto)


@login_required
@admin_required
def inventario_export_csv(request):
    productos = Producto.objects.select_related(
        'categoria',
        'subcategoria',
        'creado_por',
    ).order_by('categoria__nombre', 'nombre')
    stock_critico = request.GET.get('stock') == 'critico'
    if stock_critico:
        productos = productos.filter(
            stock_actual__lte=F('stock_minimo_alerta'),
        )

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        'attachment; filename="inventario-stock-critico.csv"'
        if stock_critico
        else 'attachment; filename="inventario.csv"'
    )
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(
        [
            'Código de barras',
            'Producto',
            'Marca',
            'Modelo',
            'Categoría',
            'Subcategoría',
            'Precio de compra',
            'Precio de venta',
            'Stock actual',
            'Stock mínimo',
            'Creado por',
        ],
    )

    def safe_csv_value(value):
        if isinstance(value, str) and value.lstrip().startswith(
            ('=', '+', '-', '@', '\t', '\r'),
        ):
            return f"'{value}"
        return value

    for producto in productos.iterator():
        row = [
            producto.codigo_barras,
            producto.nombre,
            producto.marca,
            producto.modelo,
            producto.categoria.nombre,
            producto.subcategoria.nombre if producto.subcategoria else '',
            producto.precio_compra,
            producto.precio_venta,
            producto.stock_actual,
            producto.stock_minimo_alerta,
            (
                producto.creado_por.get_full_name()
                or producto.creado_por.username
                if producto.creado_por
                else ''
            ),
        ]
        writer.writerow([safe_csv_value(value) for value in row])
    return response
