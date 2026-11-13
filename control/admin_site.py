from django.contrib.admin import AdminSite

from .models import User


class RoleBasedAdminSite(AdminSite):
    site_header = 'OptiVision'
    site_title = 'Administración | OptiVision'
    index_title = 'Gestión clínica y óptica'

    def has_permission(self, request):
        user = request.user
        return (
            user.is_active
            and user.is_staff
            and (
                user.is_superuser
                or user.rol == User.Rol.ADMINISTRADOR
            )
        )


role_admin_site = RoleBasedAdminSite(name='admin')
