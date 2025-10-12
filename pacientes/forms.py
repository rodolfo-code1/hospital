# pacientes/forms.py
from django import forms
from .models import Madre

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