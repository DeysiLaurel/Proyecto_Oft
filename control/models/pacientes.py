from django.core.validators import RegexValidator
from django.db import models


class Paciente(models.Model):
    nombre = models.CharField('nombre', max_length=100)
    apellido = models.CharField('apellido', max_length=100)
    dni = models.CharField(
        'DNI',
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'\A[0-9]{8}\Z',
                message='El DNI debe contener exactamente 8 dígitos.',
            ),
        ],
    )
    fecha_nacimiento = models.DateField('fecha de nacimiento')
    telefono = models.CharField(
        'teléfono',
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'\A[0-9]{9}\Z',
                message='El celular debe contener exactamente 9 dígitos.',
            ),
        ],
    )
    email = models.EmailField('correo electrónico', blank=True)
    direccion = models.CharField('dirección', max_length=255, blank=True)
    historial_medico_previo = models.TextField(
        'historial médico previo',
        blank=True,
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'paciente'
        verbose_name_plural = 'pacientes'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.dni})'
