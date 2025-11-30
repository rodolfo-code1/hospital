# hospital/altas/forms.py
from django import forms
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

# --- FORMULARIOS DE PROCESO DE ALTA ---

class CrearAltaForm(forms.ModelForm):
    """
    Formulario para iniciar el proceso de alta.
    Selecciona madre, parto y recién nacido existentes.
    """
    
    class Meta:
        model = Alta
        fields = ['madre', 'parto', 'recien_nacido', 'observaciones']
        widgets = {
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'parto': forms.Select(attrs={'class': 'form-select'}),
            'recien_nacido': forms.Select(attrs={'class': 'form-select'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones generales del proceso de alta'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo registros que NO tienen alta aún (alta__isnull=True)
        self.fields['madre'].queryset = Madre.objects.filter(alta__isnull=True)
        self.fields['parto'].queryset = Parto.objects.filter(alta__isnull=True)
        self.fields['recien_nacido'].queryset = RecienNacido.objects.filter(alta__isnull=True)
        
        self.fields['madre'].label = "Seleccionar Madre"
        self.fields['parto'].label = "Seleccionar Parto"
        self.fields['recien_nacido'].label = "Seleccionar Recién Nacido"
    
    def clean(self):
        cleaned_data = super().clean()
        madre = cleaned_data.get('madre')
        parto = cleaned_data.get('parto')
        recien_nacido = cleaned_data.get('recien_nacido')
        
        # Validar coherencia: el parto debe ser de esa madre
        if madre and parto:
            if parto.madre != madre:
                raise forms.ValidationError(
                    "El parto seleccionado no corresponde a la madre seleccionada."
                )
        
        # Validar coherencia: el RN debe ser de ese parto
        if parto and recien_nacido:
            if recien_nacido.parto != parto:
                raise forms.ValidationError(
                    "El recién nacido seleccionado no corresponde al parto seleccionado."
                )
        
        return cleaned_data


class ConfirmarAltaClinicaForm(forms.Form):
    """Formulario para confirmar alta clínica."""
    confirmar_alta_clinica = forms.BooleanField(
        required=True,
        label="Confirmo que el alta clínica puede ser autorizada",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    medico_nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre del médico responsable",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    observaciones_clinicas = forms.CharField(
        required=False,
        label="Observaciones clínicas adicionales",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class ConfirmarAltaAdministrativaForm(forms.Form):
    """Formulario para confirmar alta administrativa."""
    confirmar_alta_administrativa = forms.BooleanField(
        required=True,
        label="Confirmo que el alta administrativa está completa",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    administrativo_nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre del administrativo responsable",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    observaciones_administrativas = forms.CharField(
        required=False,
        label="Observaciones administrativas",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


class BuscarAltaForm(forms.Form):
    """Formulario de búsqueda y filtros para altas."""
    ESTADO_CHOICES = [('', 'Todos los estados')] + list(Alta.ESTADO_ALTA)
    
    buscar = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por RUT o nombre...'
        })
    )
    estado = forms.ChoiceField(
        required=False,
        choices=ESTADO_CHOICES,
        label="Estado",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_desde = forms.DateField(
        required=False,
        label="Fecha desde",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        label="Fecha hasta",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )