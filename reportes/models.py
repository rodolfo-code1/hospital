# hospital/reportes/models.py
from django.db import models

# NOTA DE ARQUITECTURA:
# Este módulo funciona como una capa de "Sólo Lectura" y Agregación.
# No define modelos propios porque su responsabilidad es consultar, filtrar
# y procesar los datos ya existentes en 'partos', 'pacientes', 'altas' y 'recien_nacidos'.
#
# Toda la persistencia de datos ocurre en los módulos operativos respectivos.