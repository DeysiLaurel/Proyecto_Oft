from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = 'ADMINISTRADOR', 'Administrador'
        CAJERO_VENDEDOR = 'CAJERO_VENDEDOR', 'Cajero/Vendedor'

    rol = models.CharField(
        'rol',
        max_length=20,
        choices=Rol.choices,
        default=Rol.CAJERO_VENDEDOR,
    )
    telefono = models.CharField(
        'teléfono',
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'\A[0-9]{9}\Z',
                message='Ingresa exactamente 9 dígitos numéricos.',
            ),
        ],
    )
    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return self.get_full_name() or self.username
