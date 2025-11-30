# hospital/altas/forms.py
from django import forms
from .models import Alta
from pacientes.models import Madre
from partos.models import Parto
from recien_nacidos.models import RecienNacido

class CrearAltaForm(forms.ModelForm):
    """
    Formulario inteligente: Filtra opciones según la madre seleccionada.
    """
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
        
        # 1. Cargar listas completas (de pacientes hospitalizados y sanos)
        self.fields['madre'].queryset = Madre.objects.filter(
            estado_alta='hospitalizado', estado_salud='sano'
        )
        self.fields['parto'].queryset = Parto.objects.all()
        self.fields['recien_nacido'].queryset = RecienNacido.objects.filter(
            estado_alta='hospitalizado', estado_salud='sano'
        )

        # 2. Lógica de Filtrado Inteligente (Server-Side)
        # Si hay datos en el formulario (POST) o valores iniciales (GET del panel)
        madre_id = None
        if 'madre' in self.data:
            try:
                madre_id = int(self.data.get('madre'))
            except (ValueError, TypeError):
                pass
        elif self.initial.get('madre'):
            madre_id = self.initial.get('madre')

        # Si sabemos quién es la madre, filtramos los hijos y partos
        if madre_id:
            self.fields['parto'].queryset = Parto.objects.filter(madre_id=madre_id)
            self.fields['recien_nacido'].queryset = RecienNacido.objects.filter(parto__madre_id=madre_id, estado_salud='sano')

        # Hacer campos opcionales
        self.fields['madre'].required = False
        self.fields['parto'].required = False
        self.fields['recien_nacido'].required = False
        
        self.fields['madre'].label = "Seleccionar Madre (Sana)"
        self.fields['recien_nacido'].label = "Seleccionar Recién Nacido (Sano)"

    def clean(self):
        cleaned_data = super().clean()
        madre = cleaned_data.get('madre')
        rn = cleaned_data.get('recien_nacido')
        parto = cleaned_data.get('parto')
        
        if not madre and not rn:
            raise forms.ValidationError("Debe seleccionar al menos un paciente.")
            
        # Validaciones de consistencia
        if madre and rn:
            if rn.parto.madre != madre:
                self.add_error('recien_nacido', f"El RN {rn} no es hijo de {madre}.")
        
        if madre and parto:
            if parto.madre != madre:
                self.add_error('parto', "El parto no corresponde a esta madre.")

        return cleaned_data

# (Mantenemos los otros formularios Confirmar/Buscar iguales)
class ConfirmarAltaClinicaForm(forms.Form):
    confirmar_alta_clinica = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    medico_nombre = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    observaciones_clinicas = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

class ConfirmarAltaAdministrativaForm(forms.Form):
    confirmar_alta_administrativa = forms.BooleanField(required=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    administrativo_nombre = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    observaciones_administrativas = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

class BuscarAltaForm(forms.Form):
    ESTADO_CHOICES = [('', 'Todos')] + list(Alta.ESTADO_ALTA)
    buscar = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Buscar...'}))
    estado = forms.ChoiceField(required=False, choices=ESTADO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))
    fecha_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    fecha_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))