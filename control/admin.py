from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .admin_site import role_admin_site
from .models import (
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


@admin.register(User, site=role_admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'rol',
        'telefono',
        'is_staff',
    )
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Información de OptiVision', {'fields': ('rol', 'telefono')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Información de OptiVision',
            {'fields': ('rol', 'telefono')},
        ),
    )


@admin.register(Oftalmologo, site=role_admin_site)
class OftalmologoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'apellido',
        'dni',
        'numero_colegiatura',
        'especialidad',
        'telefono',
    )
    list_filter = ('especialidad',)
    search_fields = ('nombre', 'apellido', 'dni', 'numero_colegiatura')


@admin.register(Paciente, site=role_admin_site)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'apellido',
        'dni',
        'telefono',
        'email',
        'created_at',
    )
    list_filter = ('created_at',)
    search_fields = ('nombre', 'apellido', 'dni', 'email')


@admin.register(Cita, site=role_admin_site)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'oftalmologo', 'fecha_hora', 'estado')
    list_filter = ('estado', 'fecha_hora')
    search_fields = ('paciente__nombre', 'oftalmologo__nombre')


@admin.register(ConsultaMedica, site=role_admin_site)
class ConsultaMedicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'oftalmologo', 'fecha_atencion', 'atendido_por')
    search_fields = ('paciente__nombre', 'diagnostico')
    readonly_fields = ('atendido_por',)

    def save_model(self, request, obj, form, change):
        if not obj.atendido_por_id:
            obj.atendido_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(RecetaOftalmologica, site=role_admin_site)
class RecetaOftalmologicaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'paciente',
        'oftalmologo',
        'fecha_emision',
        'esfera_od',
        'esfera_oi',
    )
    search_fields = ('paciente__nombre', 'paciente__dni')


@admin.register(Categoria, site=role_admin_site)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')


@admin.register(Subcategoria, site=role_admin_site)
class SubcategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria')


@admin.register(Producto, site=role_admin_site)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_barras',
        'nombre',
        'marca',
        'descripcion',
        'categoria',
        'precio_venta',
        'stock_actual',
        'stock_minimo_alerta',
        'creado_por',
    )
    list_filter = ('categoria',)
    search_fields = ('nombre', 'codigo_barras', 'marca')
    readonly_fields = ('creado_por',)

    def save_model(self, request, obj, form, change):
        if not obj.creado_por_id:
            obj.creado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Venta, site=role_admin_site)
class VentaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'paciente',
        'usuario',
        'fecha_venta',
        'total',
        'metodo_pago',
        'estado',
    )
    list_filter = ('estado', 'metodo_pago', 'fecha_venta')
    search_fields = ('paciente__nombre', 'paciente__dni')
    readonly_fields = ('usuario',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


@admin.register(DetalleVenta, site=role_admin_site)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')


@admin.register(ArqueoCaja, site=role_admin_site)
class ArqueoCajaAdmin(admin.ModelAdmin):
    list_display = (
        'usuario',
        'fecha_apertura',
        'fecha_cierre',
        'monto_inicial',
        'monto_cierre_real',
        'diferencia',
        'estado',
    )
    list_filter = ('estado', 'fecha_apertura')
