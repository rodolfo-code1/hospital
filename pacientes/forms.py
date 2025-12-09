from django import forms
from .models import Madre
from usuarios.validador import validar_rut
from datetime import date

class MadreForm(forms.ModelForm):
    """Formulario Base (Matrona/Admin)"""
    class Meta:
        model = Madre
        fields = [
            'rut', 'nombre', 'fecha_nacimiento', 'edad', 
            'nacionalidad', 'prevision', 'cesfam', 
            'direccion', 'comuna', 'telefono', 'email',
            'estado_salud', 'alerta_recepcion',
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'edad': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Auto'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'value': 'Chilena'}),
            'prevision': forms.Select(attrs={'class': 'form-select'}),
            'cesfam': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CESFAM de origen'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'estado_salud': forms.Select(attrs={'class': 'form-select'}),
            'alerta_recepcion': forms.Textarea(attrs={'class': 'form-control border-danger', 'rows': 2}),
            'controles_prenatales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'embarazos_anteriores': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'patologias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['edad'].required = False

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

    def clean(self):
        cleaned_data = super().clean()
        fecha_nac = cleaned_data.get('fecha_nacimiento')
        if fecha_nac:
            hoy = date.today()
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            cleaned_data['edad'] = edad
        return cleaned_data

class MadreRecepcionForm(MadreForm):
   
    class Meta(MadreForm.Meta):
        fields = [
            'rut', 'nombre', 'fecha_nacimiento', 'edad', 
            'nacionalidad', 'prevision', 'cesfam', 
            'direccion', 'comuna', 'telefono', 'email',
            'estado_salud',
            'alerta_recepcion',
            
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
            
        ]
        widgets = MadreForm.Meta.widgets.copy()
        # Personalizamos el semáforo y la alerta
        widgets['estado_salud'] = forms.RadioSelect(attrs={'class': 'btn-check semaforo-input'})
        widgets['alerta_recepcion'] = forms.Textarea(attrs={
            'class': 'form-control border-danger bg-danger-subtle',
            'placeholder': '⚠️ Escriba aquí si hay alguna condición de riesgo visible...',
            'rows': 2
        })