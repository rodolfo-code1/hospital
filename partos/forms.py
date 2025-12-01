from django import forms
from .models import Parto
from usuarios.models import Usuario # <--- Importamos el modelo de Usuarios

class PartoForm(forms.ModelForm):
    """
    Formulario para registrar un nuevo parto.
    Ahora carga listas dinámicas de médicos y matronas.
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
            'acompanante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre acompañante'}),
            
            'tuvo_complicaciones': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'complicaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            
            # Estos widgets se sobrescribirán en el __init__, pero los dejamos por defecto
            'medico_responsable': forms.Select(attrs={'class': 'form-select'}),
            'matrona_responsable': forms.Select(attrs={'class': 'form-select'}),
            
            'personal_apoyo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # --- CARGA DINÁMICA DE PROFESIONALES ---
        
        # 1. Buscamos usuarios con rol 'medico' o 'jefatura' (que a veces hacen turnos)
        medicos = Usuario.objects.filter(rol__in=['medico', 'jefatura']).order_by('first_name')
        # Creamos la lista: (Valor a guardar, Texto a mostrar)
        # Guardamos el nombre completo para que sea compatible con tu base de datos actual
        opciones_medicos = [('', 'Seleccione Médico...')] + [
            (u.get_full_name(), f"Dr(a). {u.get_full_name()}") for u in medicos
        ]
        
        # 2. Buscamos usuarios con rol 'matrona'
        matronas = Usuario.objects.filter(rol='matrona').order_by('first_name')
        opciones_matronas = [('', 'Seleccione Matrona...')] + [
            (u.get_full_name(), f"Mat. {u.get_full_name()}") for u in matronas
        ]

        # 3. Asignamos las opciones a los campos
        self.fields['medico_responsable'].widget = forms.Select(
            choices=opciones_medicos, 
            attrs={'class': 'form-select'}
        )
        self.fields['matrona_responsable'].widget = forms.Select(
            choices=opciones_matronas, 
            attrs={'class': 'form-select'}
        )