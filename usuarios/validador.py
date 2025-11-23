import re
from itertools import cycle

def validar_rut(rut):
    """
    Valida que un RUT chileno sea correcto (formato y dígito verificador).
    Retorna True si es válido, False si no.
    Acepta formatos: 12.345.678-9, 12345678-9, 123456789
    """
    # 1. Limpieza: Eliminar puntos y guiones
    rut_limpio = rut.replace('.', '').replace('-', '').upper()
    
    # Validar largo mínimo y que sean números (excepto el K final)
    if len(rut_limpio) < 2 or not re.match(r'^\d+[0-9K]$', rut_limpio):
        return False
        
    # 2. Separar cuerpo y dígito verificador (DV)
    cuerpo = rut_limpio[:-1]
    dv = rut_limpio[-1]
    
    # 3. Calcular DV esperado (Algoritmo Módulo 11)
    rev_cuerpo = map(int, reversed(cuerpo))
    factors = cycle(range(2, 8))
    s = sum(d * f for d, f in zip(rev_cuerpo, factors))
    mod = (-s) % 11
    
    dv_esperado = {10: 'K', 11: '0'}.get(mod, str(mod))
    
    return dv == dv_esperado