# recien_nacidos/forms.py
from django import forms
from .models import RecienNacido

class RecienNacidoForm(forms.ModelForm):
    """Formulario para registrar un recién nacido"""
    
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'nombre', 'sexo', 'peso', 'talla', 
            'puntuacion_vitalidad_1min', 'puntuacion_vitalidad_5min', 'puntuacion_vitalidad_10min',
            'condicion_nacimiento', 'requiere_derivacion', 'servicio_derivacion',
            'vacunas_aplicadas', 'examenes_realizados', 'observaciones'
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.5', 'max': '8', 'placeholder': 'Ej: 3.2'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '30', 'max': '70', 'placeholder': 'Ej: 50.5'}),
            'puntuacion_vitalidad_1min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10', 'placeholder': '0-10'}),
            'puntuacion_vitalidad_5min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10', 'placeholder': '0-10'}),
            'puntuacion_vitalidad_10min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10', 'placeholder': '0-10'}),
            'condicion_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            'requiere_derivacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'servicio_derivacion': forms.TextInput(attrs={'class': 'form-control'}),
            'vacunas_aplicadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'examenes_realizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }