from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import BaseFormSet, formset_factory, inlineformset_factory
from django.core.validators import MaxValueValidator, MinValueValidator

from .models import (
    ArqueoCaja,
    Categoria,
    Cita,
    ConsultaMedica,
    Oftalmologo,
    ParametrosSistema,
    Paciente,
    ProcedimientoOftalmologico,
    Producto,
    RecetaOftalmologica,
    Subcategoria,
    User,
    Venta,
)


INPUT_CLASSES = (
    'mt-1 block w-full rounded-lg border border-slate-300 bg-white px-3 py-2 '
    'text-sm text-slate-900 shadow-sm outline-none transition '
    'focus:border-clinic-600 focus:ring-2 focus:ring-clinic-100'
)


def _strict_digit_field(length, message, *, required=True):
    return forms.RegexField(
        regex=rf'\A[0-9]{{{length}}}\Z',
        strip=False,
        required=required,
        error_messages={'invalid': message},
    )


class PacienteForm(forms.ModelForm):
    dni = _strict_digit_field(
        8,
        'El DNI debe contener exactamente 8 dígitos.',
    )
    telefono = _strict_digit_field(
        9,
        'El celular debe contener exactamente 9 dígitos.',
        required=False,
    )

    class Meta:
        model = Paciente
        fields = (
            'nombre',
            'apellido',
            'dni',
            'fecha_nacimiento',
            'telefono',
            'email',
            'direccion',
            'historial_medico_previo',
        )
        widgets = {
            'fecha_nacimiento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'},
            ),
            'direccion': forms.TextInput(),
            'historial_medico_previo': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES
        self.fields['historial_medico_previo'].widget.attrs['rows'] = 4


class CitaForm(forms.ModelForm):
    fecha_hora = forms.DateTimeField(
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'},
        ),
    )

    class Meta:
        model = Cita
        fields = ('paciente', 'oftalmologo', 'fecha_hora', 'motivo_consulta')
        widgets = {'motivo_consulta': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.order_by(
            'apellido',
            'nombre',
        )
        self.fields['oftalmologo'].queryset = Oftalmologo.objects.order_by(
            'apellido',
            'nombre',
        )
        self.fields['paciente'].empty_label = 'Selecciona un paciente'
        self.fields['oftalmologo'].empty_label = 'Selecciona un oftalmólogo'
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class OftalmologoForm(forms.ModelForm):
    dni = _strict_digit_field(
        8,
        'El DNI debe contener exactamente 8 dígitos.',
    )
    telefono = _strict_digit_field(
        9,
        'El celular debe contener exactamente 9 dígitos.',
        required=False,
    )

    class Meta:
        model = Oftalmologo
        fields = (
            'nombre',
            'apellido',
            'dni',
            'numero_colegiatura',
            'especialidad',
            'telefono',
            'email',
            'horario_atencion',
        )
        widgets = {
            'horario_atencion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class UsuarioCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'rol',
            'telefono',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefono'] = _strict_digit_field(
            9,
            'El celular debe contener exactamente 9 dígitos.',
            required=False,
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = user.rol == User.Rol.ADMINISTRADOR
        if commit:
            user.save()
            self.save_m2m()
        return user


class UsuarioUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'email',
            'rol',
            'telefono',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefono'] = _strict_digit_field(
            9,
            'El celular debe contener exactamente 9 dígitos.',
            required=False,
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = user.rol == User.Rol.ADMINISTRADOR
        if commit:
            user.save()
        return user


class ParametrosSistemaForm(forms.ModelForm):
    class Meta:
        model = ParametrosSistema
        fields = (
            'nombre_optica',
            'direccion',
            'telefono',
            'ruc',
            'moneda',
            'impuesto_porcentaje',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES
        self.fields['impuesto_porcentaje'].widget.attrs.update(
            {'min': '0', 'max': '100', 'step': '0.01'},
        )


class ReportePeriodoForm(forms.Form):
    desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get('desde')
        hasta = cleaned_data.get('hasta')
        if desde and hasta and desde > hasta:
            raise forms.ValidationError(
                'La fecha inicial no puede ser posterior a la fecha final.',
            )
        return cleaned_data


class ConsultaMedicaForm(forms.ModelForm):
    class Meta:
        model = ConsultaMedica
        fields = ('sintomas', 'diagnostico', 'observaciones_clinicas')
        widgets = {
            'sintomas': forms.Textarea(attrs={'rows': 4}),
            'diagnostico': forms.Textarea(attrs={'rows': 4}),
            'observaciones_clinicas': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class ProcedimientoOftalmologicoForm(forms.ModelForm):
    class Meta:
        model = ProcedimientoOftalmologico
        fields = (
            'tipo_intervencion',
            'ojo_intervenido',
            'fecha',
            'observaciones',
        )
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES

    def clean(self):
        cleaned_data = super().clean()
        has_procedure_details = any(
            cleaned_data.get(field)
            for field in (
                'tipo_intervencion',
                'ojo_intervenido',
                'fecha',
                'observaciones',
            )
        )
        if has_procedure_details:
            for field in ('tipo_intervencion', 'ojo_intervenido', 'fecha'):
                if not cleaned_data.get(field):
                    self.add_error(field, 'Completa este dato del procedimiento.')
        return cleaned_data


ProcedimientoFormSet = inlineformset_factory(
    ConsultaMedica,
    ProcedimientoOftalmologico,
    form=ProcedimientoOftalmologicoForm,
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True,
)


class RecetaOftalmologicaForm(forms.ModelForm):
    eje_od = forms.IntegerField(
        label='Eje OD',
        min_value=0,
        max_value=180,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '180', 'step': '1'}),
    )
    eje_oi = forms.IntegerField(
        label='Eje OI',
        min_value=0,
        max_value=180,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '180', 'step': '1'}),
    )

    class Meta:
        model = RecetaOftalmologica
        fields = (
            'esfera_od',
            'cilindro_od',
            'eje_od',
            'esfera_oi',
            'cilindro_oi',
            'eje_oi',
            'adicion',
            'distancia_pupilar',
            'tipo_lente_sugerido',
        )
        widgets = {
            'esfera_od': forms.NumberInput(attrs={'step': '0.25'}),
            'cilindro_od': forms.NumberInput(attrs={'step': '0.25'}),
            'esfera_oi': forms.NumberInput(attrs={'step': '0.25'}),
            'cilindro_oi': forms.NumberInput(attrs={'step': '0.25'}),
            'adicion': forms.NumberInput(attrs={'step': '0.25'}),
            'distancia_pupilar': forms.NumberInput(attrs={'step': '0.5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eje_od'].validators.extend(
            [MinValueValidator(0), MaxValueValidator(180)],
        )
        self.fields['eje_oi'].validators.extend(
            [MinValueValidator(0), MaxValueValidator(180)],
        )
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class SubcategoriaForm(forms.ModelForm):
    class Meta:
        model = Subcategoria
        fields = ('categoria', 'nombre', 'descripcion')
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class ProductoForm(forms.ModelForm):
    MAX_IMAGE_SIZE = 5 * 1024 * 1024

    class Meta:
        model = Producto
        fields = (
            'categoria',
            'subcategoria',
            'codigo_barras',
            'nombre',
            'marca',
            'modelo',
            'descripcion',
            'imagen',
            'precio_compra',
            'precio_venta',
        )
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'imagen': forms.FileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].queryset = Categoria.objects.order_by('nombre')
        self.fields['subcategoria'].queryset = Subcategoria.objects.select_related(
            'categoria',
        ).order_by('categoria__nombre', 'nombre')
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES
        self.fields['imagen'].widget.attrs.update(
            {'class': INPUT_CLASSES, 'accept': 'image/*'},
        )
        self.fields['imagen'].required = False
        self.fields['precio_compra'].validators.append(MinValueValidator(0))
        self.fields['precio_venta'].validators.append(MinValueValidator(0))

    def clean(self):
        cleaned_data = super().clean()
        uploaded_image = self.files.get('imagen')
        if uploaded_image and uploaded_image.size > self.MAX_IMAGE_SIZE:
            self.add_error('imagen', 'La imagen no puede superar los 5 MB.')
        categoria = cleaned_data.get('categoria')
        subcategoria = cleaned_data.get('subcategoria')
        if subcategoria and categoria and subcategoria.categoria_id != categoria.pk:
            self.add_error(
                'subcategoria',
                'La subcategoría debe pertenecer a la categoría seleccionada.',
            )
        return cleaned_data


class StockForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ('stock_actual', 'stock_minimo_alerta')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.validators.append(MinValueValidator(0))
            field.widget.attrs.update(
                {
                    'class': INPUT_CLASSES,
                    'min': '0',
                    'step': '1',
                },
            )


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ('paciente', 'receta', 'metodo_pago')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paciente'].queryset = Paciente.objects.order_by(
            'apellido',
            'nombre',
        )
        self.fields['receta'].queryset = RecetaOftalmologica.objects.select_related(
            'paciente',
        ).order_by('-fecha_emision')
        self.fields['receta'].required = False
        self.fields['receta'].empty_label = 'Sin receta'
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES

    def clean(self):
        cleaned_data = super().clean()
        paciente = cleaned_data.get('paciente')
        receta = cleaned_data.get('receta')
        if receta and paciente and receta.paciente_id != paciente.pk:
            self.add_error(
                'receta',
                'La receta seleccionada no pertenece al paciente.',
            )
        return cleaned_data


class VentaItemForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.none(),
        label='Producto',
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Cantidad',
        validators=[MinValueValidator(1)],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.order_by('nombre')
        for field in self.fields.values():
            field.widget.attrs['class'] = INPUT_CLASSES


class BaseVentaItemFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        productos = [
            form.cleaned_data['producto'].pk
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        if len(productos) != len(set(productos)):
            raise forms.ValidationError(
                'Cada producto debe aparecer una sola vez en la venta.',
            )


VentaItemFormSet = formset_factory(
    VentaItemForm,
    formset=BaseVentaItemFormSet,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class ArqueoAperturaForm(forms.ModelForm):
    class Meta:
        model = ArqueoCaja
        fields = ('monto_inicial',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['monto_inicial'].validators.append(MinValueValidator(0))
        self.fields['monto_inicial'].widget.attrs.update(
            {'class': INPUT_CLASSES, 'min': '0', 'step': '0.01'},
        )


class ArqueoCierreForm(forms.Form):
    monto_cierre_real = forms.DecimalField(
        label='Monto real en caja al cierre',
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                'class': INPUT_CLASSES,
                'min': '0',
                'step': '0.01',
            },
        ),
    )
