# usuarios/forms.py
from django import forms
from .models import Usuario
from .validador import validar_rut

class RegistroUsuarioForm(forms.ModelForm):
    """Formulario usado por Encargado TI para crear una cuenta base sin contraseña."""
    
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
    
    telefono = forms.CharField(
        max_length=20,
        required=False,
        label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 4444 5555'})
    )
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'rut', 'email', 'rol', 'telefono']
        widgets = {
          'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'}),
          'rol': forms.Select(attrs={'class': 'form-select'}),
        }
    
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
      
    def clean_email(self):
      email = self.cleaned_data.get('email')
      if Usuario.objects.filter(email=email).exists():
          raise forms.ValidationError("Este correo ya está registrado.")
      return email  
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Generar username automáticamente desde el RUT
        user.username = self.cleaned_data['rut'].replace('-', '').replace('.', '')
        
        # Dividir el nombre completo en first_name y last_name
        nombre_completo = self.cleaned_data['nombre'].strip().split()
        user.first_name = nombre_completo[0]
        user.last_name = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''
        
        # Usuario queda INACTIVO hasta crear clave
        user.is_active = False
        
        if commit:
            user.save()
        return user

class EditarUsuarioForm(forms.ModelForm):
    nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre Completo",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['rut', 'email', 'telefono', 'rol', 'is_active']  # 👈 is_active sí va
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': '¿Usuario activo en el sistema?'
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if instance:
            self.fields['nombre'].initial = instance.get_full_name()

    def save(self, commit=True):
        user = super().save(commit=False)
        nombre_completo = self.cleaned_data['nombre'].split()

        user.first_name = nombre_completo[0]
        user.last_name = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''

        if commit:
            user.save()
        return user

class ResetPasswordRUTForm(forms.Form):
    rut = forms.CharField(
        max_length=12,
        label="RUT",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'})
    )