from django.db import models


class Categoria(models.Model):
    nombre = models.CharField('nombre', max_length=100, unique=True)
    descripcion = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Subcategoria(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='subcategorias',
        verbose_name='categoría',
    )
    nombre = models.CharField('nombre', max_length=100)
    descripcion = models.TextField('descripción', blank=True)

    class Meta:
        verbose_name = 'subcategoría'
        verbose_name_plural = 'subcategorías'
        ordering = ['categoria__nombre', 'nombre']

    def __str__(self):
        return f'{self.categoria.nombre} - {self.nombre}'


class Producto(models.Model):
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='categoría',
    )
    subcategoria = models.ForeignKey(
        Subcategoria,
        on_delete=models.PROTECT,
        related_name='productos',
        verbose_name='subcategoría',
        blank=True,
        null=True,
    )
    codigo_barras = models.CharField(
        'código de barras',
        max_length=100,
        unique=True,
    )
    nombre = models.CharField('nombre', max_length=150)
    marca = models.CharField('marca', max_length=100, blank=True)
    modelo = models.CharField('modelo', max_length=100, blank=True)
    descripcion = models.TextField('descripción', blank=True)
    imagen = models.ImageField(
        'imagen del producto',
        upload_to='productos/',
        blank=True,
    )
    precio_compra = models.DecimalField(
        'precio de compra',
        max_digits=10,
        decimal_places=2,
    )
    precio_venta = models.DecimalField(
        'precio de venta',
        max_digits=10,
        decimal_places=2,
    )
    stock_actual = models.IntegerField('stock actual', default=0)
    stock_minimo_alerta = models.IntegerField(
        'stock mínimo de alerta',
        default=5,
    )
    creado_por = models.ForeignKey(
        'control.User',
        on_delete=models.SET_NULL,
        related_name='productos_creados',
        verbose_name='creado por',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'producto'
        verbose_name_plural = 'productos'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.codigo_barras})'
