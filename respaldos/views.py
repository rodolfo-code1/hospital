from django.shortcuts import redirect
import datetime
from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from usuarios.decorators import encargado_ti_requerido


@login_required
@encargado_ti_requerido
def generar_respaldo(request):
    """
    Genera y descarga un respaldo completo de la base de datos (SQL Dump).
    
    Funcionalidad:
    Recorre todas las tablas del esquema actual y genera un script SQL que permite
    reconstruir la base de datos desde cero (Estructura + Datos).
    
    Seguridad:
    - Decorador @encargado_ti_requerido: CRÍTICO. Solo el personal de TI puede
      descargar la base de datos completa, ya que contiene datos sensibles
      de pacientes (Ley de Protección de Datos).
    
    Returns:
        HttpResponse: Archivo .sql adjunto para descarga inmediata.
    """
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"respaldo_{now}.sql"

    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tablas = [row[0] for row in cursor.fetchall()]

            dump = ""

            for tabla in tablas:
                # Estructura
                cursor.execute(f"SHOW CREATE TABLE `{tabla}`;")
                create_stmt = cursor.fetchone()[1]
                dump += f"\n\n-- ----------------------------\n-- Tabla `{tabla}`\n-- ----------------------------\n"
                dump += f"DROP TABLE IF EXISTS `{tabla}`;\n{create_stmt};\n"

                # Datos
                cursor.execute(f"SELECT * FROM `{tabla}`;")
                rows = cursor.fetchall()

                if rows:
                    dump += f"\n-- Datos de `{tabla}`\n"
                    for row in rows:
                        valores = ", ".join(f"'{str(v).replace('\'', '\\\'')}'" if v is not None else "NULL" for v in row)
                        dump += f"INSERT INTO `{tabla}` VALUES ({valores});\n"

        messages.success(request, "Respaldo generado correctamente y descargado.")

        response = HttpResponse(dump, content_type='application/sql')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        messages.error(request, f"Error generando respaldo. ({str(e)})")
        return redirect('app:home')