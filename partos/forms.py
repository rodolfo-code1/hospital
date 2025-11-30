from django import forms
from .models import Parto

class PartoForm(forms.ModelForm):
    """Formulario para registrar un nuevo parto (Actualizado)"""
    
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
            'medico_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'matrona_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'personal_apoyo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }