from django import forms
from .models import RecienNacido
from partos.models import Parto

class RecienNacidoForm(forms.ModelForm):
    """
    Formulario de RN con filtro inteligente.
    Solo permite registrar bebés en partos de madres que siguen hospitalizadas.
    """
    
    class Meta:
        model = RecienNacido
        fields = [
            'parto', 'nombre', 'sexo', 'peso', 'talla', 'perimetro_cefalico',
            'ap1_latidos', 'ap1_respiracion', 'ap1_tono', 'ap1_reflejos', 'ap1_color',
            'ap5_latidos', 'ap5_respiracion', 'ap5_tono', 'ap5_reflejos', 'ap5_color',
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
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'kg'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'cm'}),
            'perimetro_cefalico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'cm'}),
            
            # WIDGETS APGAR (Radio buttons)
            'ap1_latidos': forms.RadioSelect(attrs={'class': 'ap1-calc'}),
            'ap1_respiracion': forms.RadioSelect(attrs={'class': 'ap1-calc'}),
            'ap1_tono': forms.RadioSelect(attrs={'class': 'ap1-calc'}),
            'ap1_reflejos': forms.RadioSelect(attrs={'class': 'ap1-calc'}),
            'ap1_color': forms.RadioSelect(attrs={'class': 'ap1-calc'}),
            
            'ap5_latidos': forms.RadioSelect(attrs={'class': 'ap5-calc'}),
            'ap5_respiracion': forms.RadioSelect(attrs={'class': 'ap5-calc'}),
            'ap5_tono': forms.RadioSelect(attrs={'class': 'ap5-calc'}),
            'ap5_reflejos': forms.RadioSelect(attrs={'class': 'ap5-calc'}),
            'ap5_color': forms.RadioSelect(attrs={'class': 'ap5-calc'}),

            'apgar_1_min': forms.NumberInput(attrs={'class': 'form-control fw-bold text-center bg-light', 'readonly': True}),
            'apgar_5_min': forms.NumberInput(attrs={'class': 'form-control fw-bold text-center bg-light', 'readonly': True}),
            'apgar_10_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'condicion_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['parto'].queryset = Parto.objects.filter(
            madre__estado_alta='hospitalizado'
        ).order_by('-fecha_hora_inicio')
        
        self.fields['parto'].empty_label = "Seleccione Parto de Madre Activa..."

    def clean_parto(self):
        """Validación de seguridad extra"""
        parto = self.cleaned_data.get('parto')
        if parto:
            # Si alguien intenta trucar el formulario o usar uno viejo
            if parto.madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError(
                    f"La madre {parto.madre.nombre} ya fue dada de alta. No se pueden registrar más hijos a este parto."
                )
        return parto