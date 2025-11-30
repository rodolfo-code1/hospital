# pacientes/forms.py
from django import forms
from .models import Madre
from usuarios.validador import validar_rut

class MadreForm(forms.ModelForm):
    """Formulario COMPLETO para Edición (Matrona/Admin)"""
    class Meta:
        model = Madre
        fields = [
            'rut', 'nombre', 'fecha_nacimiento', 'edad', 
            'nacionalidad', 'prevision', 'cesfam', 
            'direccion', 'comuna', 'telefono', 'email',
            'alerta_recepcion',
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'value': 'Chilena'}),
            'prevision': forms.Select(attrs={'class': 'form-select'}),
            'cesfam': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CESFAM de origen'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # Datos Clínicos
            'controles_prenatales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'embarazos_anteriores': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'patologias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # Alerta
            'alerta_recepcion': forms.Textarea(attrs={'class': 'form-control border-danger', 'rows': 2}),
        }

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if not validar_rut(rut):
            raise forms.ValidationError("RUT inválido. Verifique el dígito verificador.")
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
        existe = Madre.objects.filter(rut=rut_formateado).exclude(pk=self.instance.pk).exists()
        if existe:
            raise forms.ValidationError("Ya existe una madre registrada con este RUT.")
        return rut_formateado

class MadreRecepcionForm(MadreForm):
    """
    Formulario para Recepcionistas.
    AHORA INCLUYE TODO (Hereda todos los campos de MadreForm),
    pero destaca la alerta visualmente.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar la alerta para que destaque al ingresar
        self.fields['alerta_recepcion'].widget.attrs.update({
            'class': 'form-control border-danger bg-danger-subtle',
            'placeholder': '⚠️ Ingrese observaciones críticas aquí...'
        })