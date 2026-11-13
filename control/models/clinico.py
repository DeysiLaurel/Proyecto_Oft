from django.db import models

from .oftamo import Oftalmologo
from .pacientes import Paciente


class Cita(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        ATENDIDA = 'ATENDIDA', 'Atendida'
        CANCELADA = 'CANCELADA', 'Cancelada'

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='paciente',
    )
    oftalmologo = models.ForeignKey(
        Oftalmologo,
        on_delete=models.PROTECT,
        related_name='citas',
        verbose_name='oftalmólogo',
    )
    fecha_hora = models.DateTimeField('fecha y hora')
    motivo_consulta = models.TextField('motivo de consulta')
    estado = models.CharField(
        'estado',
        max_length=10,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        verbose_name = 'cita'
        verbose_name_plural = 'citas'
        ordering = ['fecha_hora']

    def __str__(self):
        return f'Cita de {self.paciente} - {self.fecha_hora:%d/%m/%Y %H:%M}'


class ConsultaMedica(models.Model):
    cita = models.OneToOneField(
        Cita,
        on_delete=models.PROTECT,
        related_name='consulta_medica',
        verbose_name='cita',
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='consultas_medicas',
        verbose_name='paciente',
    )
    oftalmologo = models.ForeignKey(
        Oftalmologo,
        on_delete=models.PROTECT,
        related_name='consultas_medicas',
        verbose_name='oftalmólogo',
    )
    fecha_atencion = models.DateTimeField('fecha de atención')
    sintomas = models.TextField('síntomas')
    diagnostico = models.TextField('diagnóstico')
    observaciones_clinicas = models.TextField(
        'observaciones clínicas',
        blank=True,
    )
    atendido_por = models.ForeignKey(
        'control.User',
        on_delete=models.SET_NULL,
        related_name='consultas_atendidas',
        verbose_name='atendido por',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'consulta médica'
        verbose_name_plural = 'consultas médicas'
        ordering = ['-fecha_atencion']

    def __str__(self):
        return f'Consulta de {self.paciente} - {self.fecha_atencion:%d/%m/%Y}'


class ProcedimientoOftalmologico(models.Model):
    class Ojo(models.TextChoices):
        DERECHO = 'OD', 'Ojo derecho (OD)'
        IZQUIERDO = 'OI', 'Ojo izquierdo (OI)'
        AMBOS = 'AO', 'Ambos ojos'

    consulta = models.ForeignKey(
        ConsultaMedica,
        on_delete=models.CASCADE,
        related_name='procedimientos',
        verbose_name='consulta médica',
    )
    tipo_intervencion = models.CharField(
        'tipo de procedimiento o cirugía',
        max_length=150,
        blank=True,
    )
    ojo_intervenido = models.CharField(
        'ojo intervenido',
        max_length=2,
        choices=Ojo.choices,
        blank=True,
    )
    fecha = models.DateField('fecha del procedimiento', blank=True, null=True)
    observaciones = models.TextField('observaciones', blank=True)

    class Meta:
        verbose_name = 'procedimiento oftalmológico'
        verbose_name_plural = 'procedimientos oftalmológicos'
        ordering = ['-fecha', '-pk']

    def __str__(self):
        return self.tipo_intervencion or f'Procedimiento #{self.pk}'


class RecetaOftalmologica(models.Model):
    consulta = models.OneToOneField(
        ConsultaMedica,
        on_delete=models.PROTECT,
        related_name='receta_oftalmologica',
        verbose_name='consulta médica',
    )
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='recetas_oftalmologicas',
        verbose_name='paciente',
    )
    oftalmologo = models.ForeignKey(
        Oftalmologo,
        on_delete=models.PROTECT,
        related_name='recetas_oftalmologicas',
        verbose_name='oftalmólogo',
    )
    esfera_od = models.DecimalField('esfera OD', max_digits=5, decimal_places=2)
    cilindro_od = models.DecimalField(
        'cilindro OD',
        max_digits=5,
        decimal_places=2,
    )
    eje_od = models.PositiveSmallIntegerField('eje OD')
    esfera_oi = models.DecimalField('esfera OI', max_digits=5, decimal_places=2)
    cilindro_oi = models.DecimalField(
        'cilindro OI',
        max_digits=5,
        decimal_places=2,
    )
    eje_oi = models.PositiveSmallIntegerField('eje OI')
    adicion = models.DecimalField(
        'adición',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    distancia_pupilar = models.DecimalField(
        'distancia pupilar',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
    )
    tipo_lente_sugerido = models.CharField(
        'tipo de lente sugerido',
        max_length=150,
        blank=True,
    )
    fecha_emision = models.DateField('fecha de emisión', auto_now_add=True)

    class Meta:
        verbose_name = 'receta oftalmológica'
        verbose_name_plural = 'recetas oftalmológicas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f'Receta de {self.paciente} - {self.fecha_emision:%d/%m/%Y}'
