from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect

from .models import User


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if user.is_superuser or user.rol in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.warning(
                request,
                'No tienes permisos para acceder a esa sección.',
            )
            return redirect('control:dashboard')

        return wrapper

    return decorator


admin_required = role_required(User.Rol.ADMINISTRADOR)
cashier_or_admin_required = role_required(
    User.Rol.ADMINISTRADOR,
    User.Rol.CAJERO_VENDEDOR,
)
clinical_required = role_required(
    User.Rol.ADMINISTRADOR,
)
