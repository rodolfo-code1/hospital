# altas/utils.py
import os
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from datetime import datetime

def generar_certificado_pdf(alta):
    """
    Genera un certificado de alta en formato PDF.
    Retorna un HttpResponse con el PDF.
    """
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    filename = f'certificado_alta_{alta.madre.rut}_{datetime.now().strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Crear documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Título del certificado
    titulo = Paragraph("CERTIFICADO DE ALTA HOSPITALARIA", titulo_style)
    story.append(titulo)
    story.append(Spacer(1, 0.3 * inch))
    
    # Información de la madre
    story.append(Paragraph("DATOS DE LA MADRE", subtitulo_style))
    
    datos_madre = [
        ['RUT:', alta.madre.rut],
        ['Nombre:', alta.madre.nombre],
        ['Edad:', f'{alta.madre.edad} años'],
        ['Dirección:', alta.madre.direccion],
        ['Teléfono:', alta.madre.telefono],
    ]
    
    tabla_madre = Table(datos_madre, colWidths=[2*inch, 4*inch])
    tabla_madre.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(tabla_madre)
    story.append(Spacer(1, 0.3 * inch))
    
    # Información del parto
    story.append(Paragraph("INFORMACIÓN DEL PARTO", subtitulo_style))
    
    datos_parto = [
        ['Tipo de parto:', alta.parto.get_tipo_display()],
        ['Fecha y hora:', alta.parto.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')],
        ['Médico responsable:', alta.parto.medico_responsable],
        ['Matrona responsable:', alta.parto.matrona_responsable],
        ['Complicaciones:', 'Sí' if alta.parto.tuvo_complicaciones else 'No'],
    ]
    
    tabla_parto = Table(datos_parto, colWidths=[2*inch, 4*inch])
    tabla_parto.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(tabla_parto)
    story.append(Spacer(1, 0.3 * inch))
    
    # Información del recién nacido
    story.append(Paragraph("DATOS DEL RECIÉN NACIDO", subtitulo_style))
    
    datos_rn = [
        ['Código único:', alta.recien_nacido.codigo_unico],
        ['Sexo:', alta.recien_nacido.get_sexo_display()],
        ['Peso:', f'{alta.recien_nacido.peso} kg'],
        ['Talla:', f'{alta.recien_nacido.talla} cm'],
        ['Vitalidad (1/5 min):', f'{alta.recien_nacido.apgar_1_min} / {alta.recien_nacido.apgar_5_min}'],
        ['Condición:', alta.recien_nacido.get_condicion_nacimiento_display()],
    ]
    
    tabla_rn = Table(datos_rn, colWidths=[2*inch, 4*inch])
    tabla_rn.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(tabla_rn)
    story.append(Spacer(1, 0.4 * inch))
    
    # Información del alta
    story.append(Paragraph("INFORMACIÓN DEL ALTA", subtitulo_style))
    
    datos_alta = [
        ['Fecha de alta:', alta.fecha_alta.strftime('%d/%m/%Y %H:%M') if alta.fecha_alta else 'N/A'],
        ['Médico confirmante:', alta.medico_confirma],
        ['Fecha conf. clínica:', alta.fecha_confirmacion_clinica.strftime('%d/%m/%Y %H:%M') if alta.fecha_confirmacion_clinica else 'N/A'],
        ['Admin. confirmante:', alta.administrativo_confirma],
        ['Fecha conf. admin.:', alta.fecha_confirmacion_administrativa.strftime('%d/%m/%Y %H:%M') if alta.fecha_confirmacion_administrativa else 'N/A'],
    ]
    
    tabla_alta = Table(datos_alta, colWidths=[2*inch, 4*inch])
    tabla_alta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(tabla_alta)
    story.append(Spacer(1, 0.5 * inch))
    
    # Observaciones
    if alta.observaciones:
        story.append(Paragraph("OBSERVACIONES", subtitulo_style))
        obs_text = Paragraph(alta.observaciones.replace('\n', '<br/>'), styles['Normal'])
        story.append(obs_text)
        story.append(Spacer(1, 0.3 * inch))
    
    # Pie de página
    pie_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    fecha_emision = Paragraph(
        f"Certificado emitido el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
        pie_style
    )
    story.append(Spacer(1, 0.5 * inch))
    story.append(fecha_emision)
    
    # Construir PDF
    doc.build(story)
    
    # Marcar certificado como generado
    alta.certificado_generado = True
    alta.ruta_certificado = filename
    alta.save()
    
    return response


def exportar_altas_excel(altas):
    """
    Exporta una lista de altas a un archivo Excel.
    Retorna un HttpResponse con el archivo Excel.
    """
    # Crear workbook y worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Altas"
    
    # Estilos
    header_fill = PatternFill(start_color="1a365d", end_color="1a365d", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Encabezados
    headers = [
        'ID',
        'RUT Madre',
        'Nombre Madre',
        'Tipo Parto',
        'Código RN',
        'Peso RN (kg)',
        'Vitalidad RN (1/5 min)',
        'Estado Alta',
        'Alta Clínica',
        'Alta Administrativa',
        'Médico',
        'Administrativo',
        'Fecha Alta',
        'Fecha Creación'
    ]
    
    # Escribir encabezados
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
    
    # Escribir datos
    for row_num, alta in enumerate(altas, 2):
        ws.cell(row=row_num, column=1, value=alta.id)
        ws.cell(row=row_num, column=2, value=alta.madre.rut)
        ws.cell(row=row_num, column=3, value=alta.madre.nombre)
        ws.cell(row=row_num, column=4, value=alta.parto.get_tipo_display())
        ws.cell(row=row_num, column=5, value=alta.recien_nacido.codigo_unico)
        ws.cell(row=row_num, column=6, value=float(alta.recien_nacido.peso))
        ws.cell(row=row_num, column=7, value=f"{alta.recien_nacido.apgar_1_min}/{alta.recien_nacido.apgar_5_min}")
        ws.cell(row=row_num, column=8, value=alta.get_estado_display())
        ws.cell(row=row_num, column=9, value='Sí' if alta.alta_clinica_confirmada else 'No')
        ws.cell(row=row_num, column=10, value='Sí' if alta.alta_administrativa_confirmada else 'No')
        ws.cell(row=row_num, column=11, value=alta.medico_confirma or '-')
        ws.cell(row=row_num, column=12, value=alta.administrativo_confirma or '-')
        ws.cell(row=row_num, column=13, value=alta.fecha_alta.strftime('%d/%m/%Y %H:%M') if alta.fecha_alta else '-')
        ws.cell(row=row_num, column=14, value=alta.fecha_creacion.strftime('%d/%m/%Y %H:%M'))
    
    # Ajustar ancho de columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column].width = adjusted_width
    
    # Crear respuesta HTTP
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f'altas_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Guardar workbook en la respuesta
    wb.save(response)
    
    return response