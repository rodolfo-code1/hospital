from django import forms
from .models import RecienNacido

class RecienNacidoForm(forms.ModelForm):
    """Formulario para registrar un recién nacido (Actualizado Planilla URNI)"""
    
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'nombre', 'sexo', 'peso', 'talla', 'perimetro_cefalico',
            'apgar_1_min', 'apgar_5_min', 'apgar_10_min',
            'condicion_nacimiento', 
            'lactancia_precoz', 'apego_piel_a_piel', 'profilaxis_ocular',
            'vacuna_hepatitis_b', 'responsable_vacuna_vhb', 'vacuna_bcg',
            'requiere_derivacion', 'servicio_derivacion',
            'examenes_realizados', 'observaciones'
        ]
        widgets = {
            'parto': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'Kg (ej: 3.450)'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'cm'}),
            'perimetro_cefalico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'CC (cm)'}),
            
            'apgar_1_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'apgar_5_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'apgar_10_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            
            'condicion_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            
            # Checkboxes (Booleanos)
            'lactancia_precoz': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'apego_piel_a_piel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profilaxis_ocular': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacuna_hepatitis_b': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'vacuna_bcg': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requiere_derivacion': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            'responsable_vacuna_vhb': forms.TextInput(attrs={'class': 'form-control'}),
            'servicio_derivacion': forms.TextInput(attrs={'class': 'form-control'}),
            
            'examenes_realizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }