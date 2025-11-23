# pacientes/forms.py
from django import forms
from .models import Madre
from usuarios.validador import validar_rut
class MadreForm(forms.ModelForm):
    """Formulario para registrar una nueva madre"""
    
    class Meta:
        model = Madre
        fields = [
            'rut', 'nombre', 'edad', 'direccion', 'telefono', 'email',
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'edad': forms.NumberInput(attrs={'class': 'form-control', 'min': 12, 'max': 60}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56912345678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'controles_prenatales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'embarazos_anteriores': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'patologias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        
        # 1. Validar RUT
        if not validar_rut(rut):
            raise forms.ValidationError("RUT inválido. Verifique el dígito verificador.")
            
        # 2. Formatear
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
        
        # 3. Verificar duplicados (excluyendo la instancia actual si es edición)
        # self.instance.pk verifica si estamos editando una madre existente
        existe = Madre.objects.filter(rut=rut_formateado).exclude(pk=self.instance.pk).exists()
        
        if existe:
            raise forms.ValidationError("Ya existe una madre registrada con este RUT.")
            
        return rut_formateado