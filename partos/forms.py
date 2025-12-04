from django import forms
from .models import Parto, Aborto
from usuarios.models import Usuario

class PartoForm(forms.ModelForm):
    """
    Formulario para registrar parto.
    Validación Cruzada: Impide registrar parto si ya existe Parto O Aborto en este ingreso.
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
        super().__init__(*args, **kwargs)
        
        # Carga Dinámica
        medicos = Usuario.objects.filter(rol__in=['medico', 'jefatura']).order_by('first_name')
        opciones_medicos = [('', 'Seleccione Médico...')] + [
            (u.get_full_name() if u.get_full_name().strip() else u.username, 
             f"Dr(a). {u.get_full_name()}" if u.get_full_name().strip() else u.username) 
            for u in medicos
        ]
        
        matronas = Usuario.objects.filter(rol='matrona').order_by('first_name')
        opciones_matronas = [('', 'Seleccione Matrona...')] + [
            (u.get_full_name() if u.get_full_name().strip() else u.username, 
             f"Mat. {u.get_full_name()}" if u.get_full_name().strip() else u.username) 
            for u in matronas
        ]

        self.fields['medico_responsable'].widget.choices = opciones_medicos
        self.fields['matrona_responsable'].widget.choices = opciones_matronas

        # Solo madres hospitalizadas
        from pacientes.models import Madre
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado')

    def clean_madre(self):
        """VALIDACIÓN: Solo 1 evento (Parto o Aborto) por ingreso."""
        madre = self.cleaned_data.get('madre')
        
        if not madre: return None
        
        # Si es nuevo registro
        if not self.instance.pk:
            # 1. Verificar estado
            if madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError(f"Paciente {madre.nombre} no está hospitalizada.")

            # 2. Verificar si ya tiene PARTO
            if Parto.objects.filter(madre=madre, fecha_registro__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError(f"La paciente ya tiene un PARTO registrado en este ingreso.")

            # 3. Verificar si ya tiene ABORTO (Nuevo chequeo cruzado)
            if Aborto.objects.filter(madre=madre, fecha_derivacion__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError(f"La paciente ya tiene un proceso de ABORTO/IVE en curso.")
        
        return madre


class DerivacionAbortoForm(forms.ModelForm):
    """
    Formulario para derivar a médico (IVE/Aborto).
    Validación Cruzada: Impide derivar si ya hay parto o aborto.
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
        from pacientes.models import Madre
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado')

    def clean_madre(self):
        """VALIDACIÓN: Solo 1 evento (Parto o Aborto) por ingreso."""
        madre = self.cleaned_data.get('madre')
        
        if not madre: return None

        if not self.instance.pk:
            # 1. Verificar estado
            if madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError("Paciente no hospitalizada.")

            # 2. Verificar si ya tiene PARTO (No puedes abortar si ya pariste en este ingreso)
            if Parto.objects.filter(madre=madre, fecha_registro__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError("La paciente ya tiene un PARTO registrado. No corresponde derivación IVE.")

            # 3. Verificar si ya tiene ABORTO
            if Aborto.objects.filter(madre=madre, fecha_derivacion__gte=madre.fecha_ingreso).exists():
                raise forms.ValidationError("La paciente ya tiene una derivación de ABORTO/IVE registrada.")
        
        return madre


class ResolverAbortoForm(forms.ModelForm):
    """Formulario para el Médico: Resolución"""
    class Meta:
        model = Aborto
        fields = ['tipo', 'causal', 'diagnostico_final']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'causal': forms.Select(attrs={'class': 'form-select'}),
            'diagnostico_final': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }