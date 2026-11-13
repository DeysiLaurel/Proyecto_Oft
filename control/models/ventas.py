from django.db import models

from .clinico import RecetaOftalmologica
from .inventario import Producto
from .pacientes import Paciente
from .usuarios import User


class Venta(models.Model):
    class MetodoPago(models.TextChoices):
        EFECTIVO = 'EFECTIVO', 'Efectivo'
        TARJETA = 'TARJETA', 'Tarjeta'
        YAPE_PLIN = 'YAPE_PLIN', 'Yape/Plin'

    class Estado(models.TextChoices):
        COMPLETADA = 'COMPLETADA', 'Completada'
        ANULADA = 'ANULADA', 'Anulada'

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name='paciente',
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name='cajero/vendedor',
    )
    receta = models.ForeignKey(
        RecetaOftalmologica,
        on_delete=models.SET_NULL,
        related_name='ventas',
        verbose_name='receta oftalmológica',
        blank=True,
        null=True,
    )
    arqueo = models.ForeignKey(
        'ArqueoCaja',
        on_delete=models.SET_NULL,
        related_name='ventas',
        verbose_name='turno de caja',
        blank=True,
        null=True,
    )
    fecha_venta = models.DateTimeField('fecha de venta', auto_now_add=True)
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=10,
        decimal_places=2,
    )
    total = models.DecimalField('total', max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        'método de pago',
        max_length=10,
        choices=MetodoPago.choices,
    )
    estado = models.CharField(
        'estado',
        max_length=10,
        choices=Estado.choices,
        default=Estado.COMPLETADA,
    )

    class Meta:
        verbose_name = 'venta'
        verbose_name_plural = 'ventas'
        ordering = ['-fecha_venta']

    def __str__(self):
        return f'Venta #{self.pk} - {self.paciente} ({self.total})'


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta,
        on_delete=models.CASCADE,
        related_name='detalles',
        verbose_name='venta',
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='detalles_venta',
        verbose_name='producto',
    )
    cantidad = models.PositiveIntegerField('cantidad')
    precio_unitario = models.DecimalField(
        'precio unitario',
        max_digits=10,
        decimal_places=2,
    )
    subtotal = models.DecimalField(
        'subtotal',
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        verbose_name = 'detalle de venta'
        verbose_name_plural = 'detalles de venta'

    def __str__(self):
        return f'{self.producto} x {self.cantidad} (venta #{self.venta_id})'


class ArqueoCaja(models.Model):
    class Estado(models.TextChoices):
        ABIERTA = 'ABIERTA', 'Abierta'
        CERRADA = 'CERRADA', 'Cerrada'

    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='arqueos_caja',
        verbose_name='usuario',
    )
    fecha_apertura = models.DateTimeField('fecha de apertura', auto_now_add=True)
    fecha_cierre = models.DateTimeField(
        'fecha de cierre',
        blank=True,
        null=True,
    )
    monto_inicial = models.DecimalField(
        'monto inicial',
        max_digits=10,
        decimal_places=2,
    )
    total_efectivo_ventas = models.DecimalField(
        'total de ventas en efectivo',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total_tarjeta = models.DecimalField(
        'total de ventas con tarjeta',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    total_transferencias = models.DecimalField(
        'total de transferencias',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    monto_cierre_real = models.DecimalField(
        'monto real de cierre',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    diferencia = models.DecimalField(
        'diferencia',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    estado = models.CharField(
        'estado',
        max_length=7,
        choices=Estado.choices,
        default=Estado.ABIERTA,
    )

    class Meta:
        verbose_name = 'arqueo de caja'
        verbose_name_plural = 'arqueos de caja'
        ordering = ['-fecha_apertura']

    def __str__(self):
        return f'Arqueo #{self.pk} - {self.usuario} ({self.get_estado_display()})'
