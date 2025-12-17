# hospital/pacientes/forms.py
from django import forms
from .models import Madre
from usuarios.validador import validar_rut
from datetime import date

class MadreForm(forms.ModelForm):
    """
    Formulario Base para gestión de Madres.
    Utilizado por Matronas y Administrativos para editar datos completos.
    """
    class Meta:
        model = Madre
        fields = [
            'rut', 'nombre', 'fecha_nacimiento', 'edad', 
            'nacionalidad', 'prevision', 'cesfam', 
            'direccion', 'comuna', 'telefono', 'email',
            'estado_salud', 'alerta_recepcion',
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
        ]
        # Widgets estilizados con clases de Bootstrap
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            # Edad readonly porque se calcula automáticamente
            'edad': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'placeholder': 'Auto'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control', 'value': 'Chilena'}),
            'prevision': forms.Select(attrs={'class': 'form-select'}),
            'cesfam': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CESFAM de origen'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'comuna': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+569...'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'estado_salud': forms.Select(attrs={'class': 'form-select'}),
            'alerta_recepcion': forms.Textarea(attrs={'class': 'form-control border-danger', 'rows': 2}),
            'controles_prenatales': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'embarazos_anteriores': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'patologias': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La edad no es requerida en el HTML porque se calcula en el backend
        self.fields['edad'].required = False

    def clean_rut(self):
        """
        Validación y limpieza del RUT chileno.
        1. Verifica el algoritmo del dígito verificador.
        2. Formatea el RUT (elimina puntos, guiones y convierte a mayúsculas).
        3. Verifica si ya existe en la base de datos (evita duplicados).
        """
        rut = self.cleaned_data.get('rut')
        if not validar_rut(rut):
            raise forms.ValidationError("RUT inválido. Verifique el dígito verificador.")
        
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
        
        # Verificar duplicados excluyendo la propia instancia (para edición)
        existe = Madre.objects.filter(rut=rut_formateado).exclude(pk=self.instance.pk).exists()
        if existe:
            raise forms.ValidationError("Ya existe una madre registrada con este RUT.")
        return rut_formateado

    def clean(self):
        """
        Validación cruzada: Cálculo automático de edad.
        Si se proporciona fecha de nacimiento, se sobreescribe el campo edad.
        """
        cleaned_data = super().clean()
        fecha_nac = cleaned_data.get('fecha_nacimiento')
        if fecha_nac:
            hoy = date.today()
            # Cálculo preciso de edad considerando mes y día
            edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
            cleaned_data['edad'] = edad
        return cleaned_data

class MadreRecepcionForm(MadreForm):
    """
    Formulario especializado para la Recepción/Admisión.
    Hereda de MadreForm pero personaliza los widgets del 'Semáforo' de riesgo.
    """
    class Meta(MadreForm.Meta):
        fields = [
            'rut', 'nombre', 'fecha_nacimiento', 'edad', 
            'nacionalidad', 'prevision', 'cesfam', 
            'direccion', 'comuna', 'telefono', 'email',
            'estado_salud',
            'alerta_recepcion',
            'controles_prenatales', 'embarazos_anteriores', 'patologias'
        ]
        widgets = MadreForm.Meta.widgets.copy()
        
        # Personalizamos visualmente el semáforo para la recepcionista
        # Se renderiza como botones en lugar de un select dropdown
        widgets['estado_salud'] = forms.RadioSelect(attrs={'class': 'btn-check semaforo-input'})
        
        # Campo destacado en rojo para alertas de ingreso
        widgets['alerta_recepcion'] = forms.Textarea(attrs={
            'class': 'form-control border-danger bg-danger-subtle',
            'placeholder': '⚠️ Escriba aquí si hay alguna condición de riesgo visible...',
            'rows': 2
        })