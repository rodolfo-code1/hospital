# hospital/partos/forms.py
from django import forms
from .models import Parto, Aborto
from usuarios.models import Usuario
from pacientes.models import Madre

class PartoForm(forms.ModelForm):
    """
    Formulario principal para registrar un Parto.
    Utilizado por Matronas en turno.
    
    Validación de Negocio (clean_madre):
    Impide registrar un parto si:
    1. La paciente no está hospitalizada.
    2. Ya existe un parto registrado para este ingreso.
    3. Existe un proceso de Aborto/IVE activo (incoherencia clínica).
    """
    class Meta:
        model = Parto
        fields = [
            'madre', 'tipo', 'fecha_hora_inicio', 'fecha_hora_termino',
            'edad_gestacional_semanas', 'edad_gestacional_dias',
            'acompanante',
            'tuvo_complicaciones', 'complicaciones', 
            'medico_responsable', 'matrona_responsable', 'personal_apoyo', 
            'observaciones'
        ]
        widgets = {
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha_hora_inicio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_hora_termino': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'edad_gestacional_semanas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Semanas'}),
            'edad_gestacional_dias': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Días'}),
            'acompanante': forms.TextInput(attrs={'class': 'form-control'}),
            'tuvo_complicaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'complicaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medico_responsable': forms.Select(attrs={'class': 'form-select'}),
            'matrona_responsable': forms.Select(attrs={'class': 'form-select'}),
            'personal_apoyo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        """Inicializa los selectores con usuarios reales del sistema."""
        super().__init__(*args, **kwargs)
        
        # Cargar lista de médicos y jefes
        medicos = Usuario.objects.filter(rol__in=['medico', 'jefatura']).order_by('first_name')
        opciones_medicos = [('', 'Seleccione Médico...')] + [
            (u.get_full_name() if u.get_full_name().strip() else u.username, 
             f"Dr(a). {u.get_full_name()}" if u.get_full_name().strip() else u.username) 
            for u in medicos
        ]
        
        # Cargar lista de matronas
        matronas = Usuario.objects.filter(rol='matrona').order_by('first_name')
        opciones_matronas = [('', 'Seleccione Matrona...')] + [
            (u.get_full_name() if u.get_full_name().strip() else u.username, 
             f"Mat. {u.get_full_name()}" if u.get_full_name().strip() else u.username) 
            for u in matronas
        ]

        self.fields['medico_responsable'].widget.choices = opciones_medicos
        self.fields['matrona_responsable'].widget.choices = opciones_matronas

        # Filtro de seguridad: Solo madres activas en el hospital
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado')

    def clean_madre(self):
        """VALIDACIÓN CLÍNICA: Solo 1 evento (Parto o Aborto) por ingreso."""
        madre = self.cleaned_data.get('madre')
        
        if not madre: return None
        
        # Solo validamos al crear, no al editar (pk es None)
        if not self.instance.pk:
            if madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError(f"Paciente {madre.nombre} no está hospitalizada.")

            # Regla: No duplicar partos
            if Parto.objects.filter(madre=madre, fecha_registro__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError(f"La paciente ya tiene un PARTO registrado en este ingreso.")

            # Regla: Incoherencia clínica (Parto vs Aborto)
            if Aborto.objects.filter(madre=madre, fecha_derivacion__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError(f"La paciente ya tiene un proceso de ABORTO/IVE en curso.")
        
        return madre


class DerivacionAbortoForm(forms.ModelForm):
    """
    Formulario para la Matrona: Derivar caso sospechoso o IVE al Médico.
    Incluye validaciones similares para evitar duplicidad.
    """
    class Meta:
        model = Aborto
        fields = ['madre', 'observacion_matrona']
        widgets = {
            'madre': forms.Select(attrs={'class': 'form-select'}),
            'observacion_matrona': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describa síntomas o solicitud...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado')

    def clean_madre(self):
        madre = self.cleaned_data.get('madre')
        if not madre: return None

        if not self.instance.pk:
            if madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError("Paciente no hospitalizada.")
            if Parto.objects.filter(madre=madre, fecha_registro__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError("La paciente ya tiene un PARTO registrado. No corresponde derivación IVE.")
            if Aborto.objects.filter(madre=madre, fecha_derivacion__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError("La paciente ya tiene una derivación de ABORTO/IVE registrada.")
        
        return madre


class ResolverAbortoForm(forms.ModelForm):
    """
    Formulario para el Médico: Resolución del caso (Confirmar diagnóstico).
    """
    class Meta:
        model = Aborto
        fields = ['tipo', 'causal', 'diagnostico_final']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'causal': forms.Select(attrs={'class': 'form-select'}),
            'diagnostico_final': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FiltroTurnoForm(forms.Form):
    """
    Filtro para el panel 'Mi Turno' de la matrona.
    Permite visualizar registros históricos por fecha y bloque horario (Día/Noche).
    """
    fecha = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Seleccionar Fecha"
    )
    turno = forms.ChoiceField(
        choices=[('dia', 'Día (08:00 - 20:00)'), ('noche', 'Noche (20:00 - 08:00)')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Tipo de Turno"
    )