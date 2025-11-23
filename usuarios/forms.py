# usuarios/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from .validador import validar_rut

class RegistroUsuarioForm(UserCreationForm):
    """Formulario simplificado de registro - Solo campos esenciales"""
    
    nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre Completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan Pérez González'})
    )
    
    rut = forms.CharField(
        max_length=12,
        required=True,
        label="RUT",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'})
    )
    
    rol = forms.ChoiceField(
        choices=Usuario.ROLES,
        required=True,
        label="Cargo / Rol",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'rut', 'rol', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar labels de contraseñas
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Repetir Contraseña"
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Ocultar el campo username del formulario
        if 'username' in self.fields:
            self.fields['username'].widget = forms.HiddenInput()
    
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        
        # 1. Validar formato y dígito verificador
        if not validar_rut(rut):
            raise forms.ValidationError("El RUT ingresado no es válido.")
            
        # 2. Formatear para guardar limpio (sin puntos, con guión)
        # Es buena práctica guardar siempre en el mismo formato
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
        
        # 3. Validar unicidad (que no exista ya)
        if Usuario.objects.filter(rut=rut_formateado).exists():
            raise forms.ValidationError("Este RUT ya está registrado en el sistema.")
            
        return rut_formateado
    def save(self, commit=True):
        user = super().save(commit=False)
        # Generar username automáticamente desde el RUT
        user.username = self.cleaned_data['rut'].replace('-', '').replace('.', '')
        
        # Dividir el nombre completo en first_name y last_name
        nombre_completo = self.cleaned_data['nombre'].strip().split()
        if len(nombre_completo) >= 2:
            user.first_name = nombre_completo[0]
            user.last_name = ' '.join(nombre_completo[1:])
        else:
            user.first_name = nombre_completo[0] if nombre_completo else ''
            user.last_name = ''
        
        if commit:
            user.save()
        return user
# ... (código existente) ...

class EditarUsuarioForm(forms.ModelForm):
    """Formulario para que el TI modifique datos de usuarios existentes"""
    
    nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre Completo",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Usuario
        fields = ['rut', 'nombre', 'email', 'telefono', 'rol', 'is_active']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': '¿Usuario Activo?'
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            # Pre-llenar el campo nombre combinando first_name y last_name
            initial = kwargs.get('initial', {})
            initial['nombre'] = instance.get_full_name()
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        # Guardar nombre dividido
        nombre_completo = self.cleaned_data['nombre'].strip().split()
        if len(nombre_completo) >= 2:
            user.first_name = nombre_completo[0]
            user.last_name = ' '.join(nombre_completo[1:])
        else:
            user.first_name = nombre_completo[0] if nombre_completo else ''
            user.last_name = ''
        
        if commit:
            user.save()
        return user