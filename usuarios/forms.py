# hospital/usuarios/forms.py
from django import forms
from .models import Usuario
from .validador import validar_rut

class RegistroUsuarioForm(forms.ModelForm):
    """
    Formulario administrativo utilizado por el Encargado de TI.
    Permite registrar funcionarios en el sistema.
    
    Características:
    - Generación automática de 'username' basado en el RUT limpio.
    - El usuario se crea INACTIVO hasta que active su cuenta por correo.
    """
    
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
        """Validación estricta de RUT (Formato + Dígito Verificador + Unicidad)."""
        rut = self.cleaned_data.get('rut')
        
        # 1. Validar formato y dígito verificador (Módulo 11)
        if not validar_rut(rut):
            raise forms.ValidationError("El RUT ingresado no es válido.")
            
        # 2. Formatear para guardar limpio (sin puntos, con guión)
        # Esto asegura consistencia en la base de datos para búsquedas
        rut_limpio = rut.replace('.', '').replace('-', '').upper()
        rut_formateado = f"{rut_limpio[:-1]}-{rut_limpio[-1]}"
        
        # 3. Validar unicidad (que no exista ya)
        if Usuario.objects.filter(rut=rut_formateado).exists():
            raise forms.ValidationError("Este RUT ya está registrado en el sistema.")
            
        return rut_formateado
      
    def clean_email(self):
      """Validar unicidad del correo electrónico."""
      email = self.cleaned_data.get('email')
      if Usuario.objects.filter(email=email).exists():
          raise forms.ValidationError("Este correo ya está registrado.")
      return email  
    
    def save(self, commit=True):
        """
        Sobrescribe el guardado para configurar campos automáticos.
        """
        user = super().save(commit=False)
        
        # Generar username automáticamente desde el RUT (ej: 123456789)
        # Esto facilita el login ya que el usuario ingresa su RUT.
        user.username = self.cleaned_data['rut'].replace('-', '').replace('.', '')
        
        # Dividir el nombre completo en first_name y last_name para Django
        nombre_completo = self.cleaned_data['nombre'].strip().split()
        user.first_name = nombre_completo[0]
        user.last_name = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''
        
        # Usuario queda INACTIVO hasta crear clave vía link de correo
        user.is_active = False
        
        if commit:
            user.save()
        return user

class EditarUsuarioForm(forms.ModelForm):
    """
    Formulario para modificar datos de un usuario existente.
    Permite activar/desactivar cuentas (bloqueo de acceso).
    """
    nombre = forms.CharField(
        max_length=200,
        required=True,
        label="Nombre Completo",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Usuario
        fields = ['rut', 'email', 'telefono', 'rol', 'is_active']  
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
        # Pre-llenar el campo nombre compuesto
        if instance:
            self.fields['nombre'].initial = instance.get_full_name()

    def save(self, commit=True):
        user = super().save(commit=False)
        # Actualizar nombres separados
        nombre_completo = self.cleaned_data['nombre'].split()
        user.first_name = nombre_completo[0]
        user.last_name = ' '.join(nombre_completo[1:]) if len(nombre_completo) > 1 else ''

        if commit:
            user.save()
        return user

class ResetPasswordRUTForm(forms.Form):
    """Formulario simple para solicitar reseteo de clave ingresando solo el RUT."""
    rut = forms.CharField(
        max_length=12,
        label="RUT",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'})
    )