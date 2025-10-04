# altas/forms.py
from django import forms
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

class CrearAltaForm(forms.ModelForm):
    """
    Formulario para iniciar el proceso de alta.
    Selecciona madre, parto y recién nacido.
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
        # Filtrar solo madres que no tienen alta aún
        self.fields['madre'].queryset = Madre.objects.filter(alta__isnull=True)
        self.fields['parto'].queryset = Parto.objects.filter(alta__isnull=True)
        self.fields['recien_nacido'].queryset = RecienNacido.objects.filter(alta__isnull=True)
        
        # Labels en español
        self.fields['madre'].label = "Seleccionar Madre"
        self.fields['parto'].label = "Seleccionar Parto"
        self.fields['recien_nacido'].label = "Seleccionar Recién Nacido"
        self.fields['observaciones'].label = "Observaciones"
    
    def clean(self):
        cleaned_data = super().clean()
        madre = cleaned_data.get('madre')
        parto = cleaned_data.get('parto')
        recien_nacido = cleaned_data.get('recien_nacido')
        
        # Validar que el parto pertenece a la madre seleccionada
        if madre and parto:
            if parto.madre != madre:
                raise forms.ValidationError(
                    "El parto seleccionado no corresponde a la madre seleccionada."
                )
        
        # Validar que el recién nacido pertenece al parto seleccionado
        if parto and recien_nacido:
            if recien_nacido.parto != parto:
                raise forms.ValidationError(
                    "El recién nacido seleccionado no corresponde al parto seleccionado."
                )
        
        return cleaned_data


class ConfirmarAltaClinicaForm(forms.Form):
    """
    Formulario simple para confirmar alta clínica.
    """
    
    confirmar_alta_clinica = forms.BooleanField(
        required=True,
        label="Confirmo que el alta clínica puede ser autorizada",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    medico_nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre del médico responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Dr. Juan Pérez'
        })
    )
    
    observaciones_clinicas = forms.CharField(
        required=False,
        label="Observaciones clínicas adicionales",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Indicaciones médicas, recomendaciones, etc.'
        })
    )


class ConfirmarAltaAdministrativaForm(forms.Form):
    """
    Formulario simple para confirmar alta administrativa.
    """
    
    confirmar_alta_administrativa = forms.BooleanField(
        required=True,
        label="Confirmo que el alta administrativa está completa",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    administrativo_nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre del administrativo responsable",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: María González'
        })
    )
    
    observaciones_administrativas = forms.CharField(
        required=False,
        label="Observaciones administrativas",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Documentos entregados, pendientes, etc.'
        })
    )


class BuscarAltaForm(forms.Form):
    """
    Formulario de búsqueda y filtros para altas.
    """
    
    ESTADO_CHOICES = [('', 'Todos los estados')] + list(Alta.ESTADO_ALTA)
    
    buscar = forms.CharField(
        required=False,
        label="Buscar",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por RUT o nombre de madre...'
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
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        label="Fecha hasta",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )