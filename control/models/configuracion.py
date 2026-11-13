from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class ParametrosSistema(models.Model):
    nombre_optica = models.CharField(
        'nombre de la óptica',
        max_length=150,
        default='OptiVision',
    )
    direccion = models.CharField('dirección', max_length=255, blank=True)
    telefono = models.CharField(
        'teléfono',
        max_length=9,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'\A[0-9]{9}\Z',
                message='El teléfono debe contener exactamente 9 dígitos.',
            ),
        ],
    )
    ruc = models.CharField(
        'RUC',
        max_length=11,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'\A[0-9]{11}\Z',
                message='El RUC debe contener exactamente 11 dígitos.',
            ),
        ],
    )
    moneda = models.CharField('moneda', max_length=10, default='S/')
    impuesto_porcentaje = models.DecimalField(
        'impuesto (%)',
        max_digits=5,
        decimal_places=2,
        default=18,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        verbose_name = 'parámetro del sistema'
        verbose_name_plural = 'parámetros del sistema'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        parameters, _ = cls.objects.get_or_create(pk=1)
        return parameters

    def __str__(self):
        return self.nombre_optica
