from django.urls import path

from . import views


app_name = 'control'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('administracion/usuarios/', views.usuarios_list, name='usuarios_list'),
    path(
        'administracion/usuarios/nuevo/',
        views.usuario_create,
        name='usuario_create',
    ),
    path(
        'administracion/usuarios/<int:pk>/editar/',
        views.usuario_update,
        name='usuario_update',
    ),
    path(
        'administracion/usuarios/<int:pk>/eliminar/',
        views.usuario_delete,
        name='usuario_delete',
    ),
    path(
        'administracion/configuracion/',
        views.configuracion,
        name='configuracion',
    ),
    path('administracion/reportes/', views.reportes, name='reportes'),
    path('oftalmologos/', views.oftalmologos_list, name='oftalmologos_list'),
    path(
        'oftalmologos/nuevo/',
        views.oftalmologo_create,
        name='oftalmologo_create',
    ),
    path(
        'oftalmologos/<int:pk>/editar/',
        views.oftalmologo_update,
        name='oftalmologo_update',
    ),
    path(
        'oftalmologos/<int:pk>/eliminar/',
        views.oftalmologo_delete,
        name='oftalmologo_delete',
    ),
    path('pacientes/', views.pacientes_list, name='pacientes_list'),
    path('pacientes/nuevo/', views.paciente_create, name='paciente_create'),
    path(
        'pacientes/<int:pk>/',
        views.paciente_detail,
        name='paciente_detail',
    ),
    path(
        'pacientes/<int:pk>/editar/',
        views.paciente_update,
        name='paciente_update',
    ),
    path(
        'pacientes/<int:pk>/eliminar/',
        views.paciente_delete,
        name='paciente_delete',
    ),
    path('citas/', views.citas_list, name='citas_list'),
    path('citas/nueva/', views.cita_create, name='cita_create'),
    path(
        'citas/<int:cita_pk>/consulta/',
        views.consulta_form,
        name='consulta_form',
    ),
    path(
        'consultas/<int:consulta_pk>/receta/',
        views.receta_form,
        name='receta_form',
    ),
    path(
        'recetas/<int:receta_pk>/imprimir/',
        views.receta_print,
        name='receta_print',
    ),
    path(
        'recetas/<int:receta_pk>/descargar-pdf/',
        views.receta_pdf,
        name='receta_pdf',
    ),
    path('recetas/', views.recetas_list, name='recetas_list'),
    path('productos/', views.productos_list, name='productos_list'),
    path('inventario/', views.inventario_list, name='inventario_list'),
    path(
        'inventario/<int:pk>/stock/',
        views.inventario_update_stock,
        name='inventario_update_stock',
    ),
    path(
        'inventario/exportar.csv',
        views.inventario_export_csv,
        name='inventario_export_csv',
    ),
    path('inventario/nuevo/', views.producto_create, name='producto_create'),
    path(
        'inventario/<int:pk>/editar/',
        views.producto_update,
        name='producto_update',
    ),
    path(
        'productos/<int:pk>/eliminar/',
        views.producto_delete,
        name='producto_delete',
    ),
    path(
        'inventario/categorias/nueva/',
        views.categoria_create,
        name='categoria_create',
    ),
    path(
        'inventario/categorias/<int:pk>/editar/',
        views.categoria_update,
        name='categoria_update',
    ),
    path(
        'inventario/categorias/<int:pk>/eliminar/',
        views.categoria_delete,
        name='categoria_delete',
    ),
    path(
        'inventario/subcategorias/nueva/',
        views.subcategoria_create,
        name='subcategoria_create',
    ),
    path(
        'inventario/subcategorias/<int:pk>/editar/',
        views.subcategoria_update,
        name='subcategoria_update',
    ),
    path(
        'inventario/subcategorias/<int:pk>/eliminar/',
        views.subcategoria_delete,
        name='subcategoria_delete',
    ),
    path('ventas/', views.ventas_list, name='ventas_list'),
    path('ventas/nueva/', views.venta_create, name='venta_create'),
    path('caja/arqueo/', views.arqueo_caja, name='arqueo_caja'),
    path(
        'caja/arqueos/historial/',
        views.arqueo_caja_historial,
        name='arqueo_caja_historial',
    ),
    path(
        'caja/arqueo/<int:pk>/cerrar/',
        views.arqueo_caja_cerrar,
        name='arqueo_caja_cerrar',
    ),
]
