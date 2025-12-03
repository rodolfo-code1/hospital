from django import forms
from .models import Parto
from usuarios.models import Usuario

class PartoForm(forms.ModelForm):
    """
    Formulario para registrar parto.
    Incluye validación de lógica de negocio: 1 Parto por Ingreso.
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
        
        # 1. Carga Dinámica de Profesionales
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

        # 2. Filtrar Madres: Solo mostrar las que están HOSPITALIZADAS
        from pacientes.models import Madre
        self.fields['madre'].queryset = Madre.objects.filter(estado_alta='hospitalizado')

    def clean_madre(self):
        """
        VALIDACIÓN CRÍTICA:
        1. La madre debe estar 'hospitalizado'.
        2. No puede tener otro parto registrado DESDE su fecha de ingreso actual.
        """
        madre = self.cleaned_data.get('madre')
        
        if not madre:
            return None

        if not self.instance.pk: # Solo validamos al CREAR un nuevo registro
            
            # Regla 1: Estado
            if madre.estado_alta != 'hospitalizado':
                raise forms.ValidationError(
                    f"La paciente {madre.nombre} no figura como hospitalizada. Debe realizar el proceso de Admisión/Reingreso primero."
                )

            # Regla 2: Unicidad en el ingreso actual
            # Buscamos si existe algún parto registrado DESPUÉS o IGUAL a la fecha de ingreso de la madre
            parto_existente = Parto.objects.filter(
                madre=madre,
                fecha_registro__gte=madre.fecha_ingreso
            ).exists()
            
            if parto_existente:
                raise forms.ValidationError(
                    f"La paciente {madre.nombre} ya tiene un parto registrado en este ingreso ({madre.fecha_ingreso.strftime('%d/%m/%Y')}). "
                    "Si es un nuevo embarazo, debe darla de alta y reingresarla."
                )
        
        return madre