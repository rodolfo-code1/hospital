# hospital/altas/forms.py
from django import forms
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

# ... (CrearAltaForm se mantiene igual por ahora) ...
class CrearAltaForm(forms.ModelForm):
    # ... (tu código actual de CrearAltaForm) ...
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

    def clean(self):
        cleaned_data = super().clean()
        madre = cleaned_data.get('madre')
        rn = cleaned_data.get('recien_nacido')
        if not madre and not rn:
            raise forms.ValidationError("Debe seleccionar al menos un paciente.")
        return cleaned_data


class ConfirmarAltaClinicaForm(forms.Form):
    confirmar_alta_clinica = forms.BooleanField(
        required=True, 
        label="Confirmo que el alta clínica puede ser autorizada", 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    medico_nombre = forms.CharField(
        max_length=200, 
        required=True, 
        label="Médico Responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-light', # Fondo gris claro
            'readonly': 'readonly',           # Bloqueado para edición
            'id': 'medico_nombre'
        })
    )
    
    observaciones_clinicas = forms.CharField(
        required=False, 
        label="Observaciones / Indicaciones",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
# ... (ConfirmarAltaAdministrativaForm y BuscarAltaForm se mantienen igual) ...
class ConfirmarAltaAdministrativaForm(forms.Form):
    """
    Formulario para confirmar alta administrativa.
    El nombre se carga automáticamente.
    """
    confirmar_alta_administrativa = forms.BooleanField(
        required=True, 
        label="Confirmo que el alta administrativa está completa", 
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    administrativo_nombre = forms.CharField(
        max_length=200, 
        required=True, 
        label="Administrativo Responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-light', # Fondo gris
            'readonly': 'readonly',           # Bloqueado
            'id': 'administrativo_nombre'
        })
    )
    
    observaciones_administrativas = forms.CharField(
        required=False, 
        label="Observaciones de Cierre",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
class BuscarAltaForm(forms.Form):
    ESTADO_CHOICES = [('', 'Todos')] + list(Alta.ESTADO_ALTA)
    buscar = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar...'}))
    estado = forms.ChoiceField(required=False, choices=ESTADO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))