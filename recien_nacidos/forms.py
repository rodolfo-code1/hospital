# hospital/recien_nacidos/forms.py
from django import forms
from .models import RecienNacido
from partos.models import Parto

class RecienNacidoForm(forms.ModelForm):
    """
    Formulario de ingreso clínico del Recién Nacido.
    
    Características:
    - Filtro de Partos: Solo permite seleccionar partos de madres que aún están hospitalizadas.
    - Widgets Apgar: Usa botones de opción (RadioSelect) para agilizar el ingreso en tabletas/móviles.
    - Campos de sólo lectura: Los totales de Apgar se muestran pero no se editan (se calculan vía JS/Backend).
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
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional (Ej: Hijo de...)'}),
            'sexo': forms.Select(attrs={'class': 'form-select'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001', 'placeholder': 'kg'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'cm'}),
            'perimetro_cefalico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'cm'}),
            
            # WIDGETS APGAR: Clases CSS 'ap1-calc' y 'ap5-calc' son usadas por JavaScript
            # para sumar los puntos en tiempo real en el frontend.
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

            # Campos de total en gris (readonly)
            'apgar_1_min': forms.NumberInput(attrs={'class': 'form-control fw-bold text-center bg-light', 'readonly': True}),
            'apgar_5_min': forms.NumberInput(attrs={'class': 'form-control fw-bold text-center bg-light', 'readonly': True}),
            'apgar_10_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '10'}),
            'condicion_nacimiento': forms.Select(attrs={'class': 'form-select'}),
            
            # Checkboxes estilizados
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
        """
        Inicializa el formulario aplicando filtros de negocio.
        Solo muestra partos recientes de madres que no han sido dadas de alta.
        """
        super().__init__(*args, **kwargs)
        
        self.fields['parto'].queryset = Parto.objects.filter(
            madre__estado_alta='hospitalizado'
        ).order_by('-fecha_hora_inicio')
        
        self.fields['parto'].empty_label = "Seleccione Parto de Madre Activa..."

    def clean_parto(self):
        """
        Validación de seguridad adicional:
        Impide registrar un RN si la madre ya fue dada de alta (evita incoherencias).
        """
        parto = self.cleaned_data.get('parto')
        if parto:
            if parto.madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError(
                    f"La madre {parto.madre.nombre} ya fue dada de alta. No se pueden registrar más hijos a este parto."
                )
        return parto