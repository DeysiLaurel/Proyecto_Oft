from django.core.validators import RegexValidator
from django.db import models


class Oftalmologo(models.Model):
    class Especialidad(models.TextChoices):
        GENERAL = 'Oftalmología General', 'Oftalmología General'
        OPTOMETRIA = (
            'Optometría Clínica y Refracción',
            'Optometría Clínica y Refracción',
        )
        PEDIATRICA = (
            'Oftalmología Pediátrica y Estrabismo',
            'Oftalmología Pediátrica y Estrabismo',
        )
        REFRACTIVA = (
            'Cirugía Refractiva y Segmento Anterior',
            'Cirugía Refractiva y Segmento Anterior',
        )
        RETINA_GLAUCOMA = (
            'Retina y Vítreo / Glaucoma',
            'Retina y Vítreo / Glaucoma',
        )

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
    numero_colegiatura = models.CharField(
        'número de colegiatura (CMP/COP)',
        max_length=30,
        unique=True,
    )
    especialidad = models.CharField(
        'especialidad',
        max_length=150,
        choices=Especialidad.choices,
        default=Especialidad.GENERAL,
    )
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
    horario_atencion = models.TextField('horario de atención', blank=True)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'oftalmólogo'
        verbose_name_plural = 'oftalmólogos'
        ordering = ['apellido', 'nombre']

    def __str__(self):
        return f'{self.nombre} {self.apellido} ({self.numero_colegiatura})'
