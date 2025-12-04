from django import forms
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

# (CrearAltaForm se mantiene igual)
class CrearAltaForm(forms.ModelForm):
    class Meta:
        model = Alta
        fields = ['madre', 'parto', 'recien_nacido', 'observaciones']
        widgets = {
            'madre': forms.Select(attrs={'class': 'form-select', 'id': 'id_madre'}),
            'parto': forms.Select(attrs={'class': 'form-select', 'id': 'id_parto'}),
            'recien_nacido': forms.Select(attrs={'class': 'form-select', 'id': 'id_recien_nacido'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado', estado_salud='sano')
        self.fields['recien_nacido'].queryset = RecienNacido.objects.filter(estado_alta='hospitalizado', estado_salud='sano')
        self.fields['parto'].queryset = Parto.objects.all()
        
        self.fields['madre'].required = False
        self.fields['parto'].required = False
        self.fields['recien_nacido'].required = False
        self.fields['madre'].label = "Seleccionar Madre (Sana)"
        self.fields['recien_nacido'].label = "Seleccionar Recién Nacido (Sano)"

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('madre') and not cleaned_data.get('recien_nacido'):
            raise forms.ValidationError("Debe seleccionar al menos un paciente.")
        return cleaned_data


class ConfirmarAltaClinicaForm(forms.Form):
    """
    Formulario actualizado: Auto-firma médica y registro de Anticonceptivos.
    """
    confirmar_alta_clinica = forms.BooleanField(
        required=True, 
        label="Doy fe que los pacientes cumplen criterios de alta.", 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    medico_nombre = forms.CharField(
        max_length=200, 
        required=True, 
        label="Médico Responsable",
        widget=forms.TextInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'})
    )
    
    # --- SECCIÓN ANTICONCEPTIVOS ---
    se_entrego_anticonceptivo = forms.BooleanField(
        required=False, 
        label="¿Se entrega método anticonceptivo (MAC)?",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'check_mac'})
    )
    
    metodo_anticonceptivo = forms.ChoiceField(
        required=False,
        choices=Alta.METODOS_ANTICONCEPTIVOS,
        label="Método Seleccionado",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'select_mac', 'disabled': 'true'})
    )
    # -------------------------------
    
    observaciones_clinicas = forms.CharField(
        required=False, 
        label="Indicaciones Finales",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Indicaciones de egreso...'})
    )


class ConfirmarAltaAdministrativaForm(forms.Form):
    confirmar_alta_administrativa = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    administrativo_nombre = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control bg-light', 'readonly': 'readonly'}))
    observaciones_administrativas = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

class BuscarAltaForm(forms.Form):
    ESTADO_CHOICES = [('', 'Todos')] + list(Alta.ESTADO_ALTA)
    buscar = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar...'}))
    estado = forms.ChoiceField(required=False, choices=ESTADO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))