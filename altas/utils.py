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
from django.utils import timezone

def generar_certificado_pdf(alta):
    """
    Genera un certificado de alta en formato PDF.
    Incluye datos de pacientes, parto y planificación familiar.
    """
    # Configuración de la respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    
    # Nombre dinámico del archivo
    if alta.madre and alta.recien_nacido:
        sufijo = f"{alta.madre.rut}_RN"
    elif alta.madre:
        sufijo = f"{alta.madre.rut}"
    elif alta.recien_nacido:
        sufijo = f"RN_{alta.recien_nacido.codigo_unico}"
    else:
        sufijo = f"Alta_{alta.id}"
        
    fecha_hoy = timezone.localtime(timezone.now())
    filename = f'certificado_alta_{sufijo}_{fecha_hoy.strftime("%Y%m%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Crear documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # --- ESTILOS PERSONALIZADOS ---
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a365d'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5282'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    texto_normal = styles['Normal']
    
    # --- ENCABEZADO ---
    story.append(Paragraph("CERTIFICADO DE ALTA HOSPITALARIA", titulo_style))
    story.append(Spacer(1, 0.2 * inch))
    
    intro = f"El Hospital Clínico Herminda Martín certifica que el proceso de alta médica y administrativa ha concluido exitosamente con fecha {alta.fecha_alta.strftime('%d/%m/%Y a las %H:%M')}."
    story.append(Paragraph(intro, texto_normal))
    story.append(Spacer(1, 0.3 * inch))
    
    # --- SECCIÓN 1: MADRE ---
    if alta.madre:
        story.append(Paragraph("DATOS DE LA MADRE", subtitulo_style))
        
        datos_madre = [
            ['Nombre Completo:', alta.madre.nombre],
            ['RUT:', alta.madre.rut],
            ['Edad:', f'{alta.madre.edad} años'],
            ['Previsión:', alta.madre.get_prevision_display()],
            ['Dirección:', f"{alta.madre.direccion}, {alta.madre.comuna}"],
        ]
        
        tabla_madre = Table(datos_madre, colWidths=[2*inch, 4*inch])
        tabla_madre.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(tabla_madre)
        story.append(Spacer(1, 0.2 * inch))

    # --- SECCIÓN 2: RECIÉN NACIDO ---
    if alta.recien_nacido:
        story.append(Paragraph("DATOS DEL RECIÉN NACIDO", subtitulo_style))
        
        datos_rn = [
            ['Código ID:', alta.recien_nacido.codigo_unico],
            ['Sexo:', alta.recien_nacido.get_sexo_display()],
            ['Peso al Nacer:', f'{alta.recien_nacido.peso} kg'],
            ['Talla:', f'{alta.recien_nacido.talla} cm'],
            ['APGAR (1/5):', f'{alta.recien_nacido.apgar_1_min} / {alta.recien_nacido.apgar_5_min}'],
        ]
        
        tabla_rn = Table(datos_rn, colWidths=[2*inch, 4*inch])
        tabla_rn.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e8f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(tabla_rn)
        story.append(Spacer(1, 0.2 * inch))

    # --- SECCIÓN 3: PARTO ---
    if alta.parto:
        story.append(Paragraph("ANTECEDENTES DEL PARTO", subtitulo_style))
        
        datos_parto = [
            ['Tipo:', alta.parto.get_tipo_display()],
            ['Fecha:', alta.parto.fecha_hora_inicio.strftime('%d/%m/%Y')],
            ['Médico:', alta.parto.medico_responsable],
            ['Matrona:', alta.parto.matrona_responsable],
        ]
        
        tabla_parto = Table(datos_parto, colWidths=[2*inch, 4*inch])
        tabla_parto.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f7fafc')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ]))
        story.append(tabla_parto)
        story.append(Spacer(1, 0.2 * inch))

    # --- SECCIÓN 4: PLANIFICACIÓN FAMILIAR (NUEVO) ---
    # Solo mostramos esta sección si se marcó que se entregó un método
    if alta.se_entrego_anticonceptivo:
        story.append(Paragraph("PLANIFICACIÓN FAMILIAR / MAC", subtitulo_style))
        
        datos_mac = [
            ['Método Entregado:', alta.get_metodo_anticonceptivo_display()],
            ['Estado:', 'Suministrado al alta'],
        ]
        
        tabla_mac = Table(datos_mac, colWidths=[2*inch, 4*inch])
        tabla_mac.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e6fffa')), # Color suave distintivo
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(tabla_mac)
        story.append(Spacer(1, 0.2 * inch))

    # --- SECCIÓN 5: RESPONSABLES ---
    story.append(Paragraph("RESPONSABLES DEL ALTA", subtitulo_style))
    
    datos_alta = [
        ['Alta Médica:', alta.medico_confirma or '-'],
        ['Fecha Clínica:', alta.fecha_confirmacion_clinica.strftime('%d/%m/%Y %H:%M') if alta.fecha_confirmacion_clinica else '-'],
        ['Cierre Administrativo:', alta.administrativo_confirma or '-'],
        ['Fecha Admin:', alta.fecha_confirmacion_administrativa.strftime('%d/%m/%Y %H:%M') if alta.fecha_confirmacion_administrativa else '-'],
    ]
    
    tabla_alta = Table(datos_alta, colWidths=[2*inch, 4*inch])
    tabla_alta.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(tabla_alta)
    story.append(Spacer(1, 0.5 * inch))
    
    # Observaciones Finales
    if alta.observaciones:
        story.append(Paragraph("OBSERVACIONES / INDICACIONES", subtitulo_style))
        obs_text = Paragraph(alta.observaciones.replace('\n', '<br/>'), texto_normal)
        story.append(obs_text)
    
    # Pie de página
    pie_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    fecha_emision = Paragraph(
        f"Documento generado el {fecha_hoy.strftime('%d/%m/%Y a las %H:%M')}",
        pie_style
    )
    story.append(Spacer(1, 0.5 * inch))
    story.append(fecha_emision)
    
    # Construir PDF
    doc.build(story)
    
    return response


def exportar_altas_excel(altas):
    """
    Exporta lista de altas a Excel.
    Incluye columnas de Planificación Familiar.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registro de Altas"
    
    # Estilos
    header_fill = PatternFill(start_color="1a365d", end_color="1a365d", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    headers = [
        'Folio', 'Tipo Alta', 'RUT Madre', 'Nombre Madre', 
        'Código RN', 'Sexo RN', 
        'Entrega MAC', 'Método MAC', # <--- NUEVAS COLUMNAS
        'Médico Resp.', 'Admin Resp.', 'Fecha Alta', 'Estado'
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
        # Determinar tipo
        tipo = "Conjunta"
        if not alta.madre: tipo = "Solo RN"
        if not alta.recien_nacido: tipo = "Solo Madre"
        
        # Datos seguros
        rut_madre = alta.madre.rut if alta.madre else "-"
        nom_madre = alta.madre.nombre if alta.madre else "-"
        
        cod_rn = alta.recien_nacido.codigo_unico if alta.recien_nacido else "-"
        sexo_rn = alta.recien_nacido.get_sexo_display() if alta.recien_nacido else "-"
        
        # Datos de MAC
        mac_entregado = "SÍ" if alta.se_entrego_anticonceptivo else "NO"
        mac_metodo = alta.get_metodo_anticonceptivo_display() if alta.se_entrego_anticonceptivo else "-"

        ws.cell(row=row_num, column=1, value=alta.id)
        ws.cell(row=row_num, column=2, value=tipo)
        ws.cell(row=row_num, column=3, value=rut_madre)
        ws.cell(row=row_num, column=4, value=nom_madre)
        ws.cell(row=row_num, column=5, value=cod_rn)
        ws.cell(row=row_num, column=6, value=sexo_rn)
        ws.cell(row=row_num, column=7, value=mac_entregado)
        ws.cell(row=row_num, column=8, value=mac_metodo)
        ws.cell(row=row_num, column=9, value=alta.medico_confirma or '-')
        ws.cell(row=row_num, column=10, value=alta.administrativo_confirma or '-')
        ws.cell(row=row_num, column=11, value=alta.fecha_alta.strftime('%d/%m/%Y %H:%M') if alta.fecha_alta else '-')
        ws.cell(row=row_num, column=12, value=alta.get_estado_display())
    
    # Ajustar ancho columnas
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f'reporte_altas_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb.save(response)
    return response
