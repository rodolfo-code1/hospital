# reportes/pdf_export.py
"""
Módulo para exportar reportes REM a formato PDF.
Incluye generación de PDFs para secciones individuales y exportación completa.
Las fechas se filtran usando los campos correctos del modelo.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from django.http import HttpResponse
from django.db.models import Count, Avg
from partos.models import Parto, Aborto
from recien_nacidos.models import RecienNacido
from altas.models import Alta
from pacientes.models import Madre


def crear_pdf_seccion_a(fecha_inicio, fecha_fin):
    """
    Genera el PDF para la Sección A: Información General de Partos.
    
    Estructura del Informe:
    1. Título y periodo consultado.
    2. Tabla Resumen: Tipos de parto cruzado con edad materna y peso del RN.
    3. Tablas Específicas: Prematuros, Apego, Lactancia, Nacionalidad, Acompañamiento.
    
    Args:
        fecha_inicio (date): Inicio del rango de filtro.
        fecha_fin (date): Fin del rango de filtro.
        
    Returns:
        BytesIO: Buffer en memoria que contiene el archivo PDF binario.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    elements.append(Paragraph("SECCIÓN A: INFORMACIÓN GENERAL DE PARTOS", title_style))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    partos = Parto.objects.filter(fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin])
    total_partos = partos.count()
    
    data = [['Característica', 'Total', 'Menor 15', '15-19', '20-34', 'Mayor 35', 'RN <2.5kg', 'RN ≥2.5kg']]
    data.append(['Total de Partos', str(total_partos), '', '', '', '', '', ''])
    
    tipos_partos = partos.values('tipo').annotate(count=Count('id')).order_by('tipo')
    for tipo_parto in tipos_partos:
        tipo = tipo_parto['tipo'] or 'Sin especificar'
        count = tipo_parto['count']
        
        partos_tipo = partos.filter(tipo=tipo_parto['tipo'] if tipo_parto['tipo'] else None)
        
        edad_menores_15 = partos_tipo.filter(madre__edad__lt=15).count()
        edad_15_19 = partos_tipo.filter(madre__edad__gte=15, madre__edad__lte=19).count()
        edad_20_34 = partos_tipo.filter(madre__edad__gte=20, madre__edad__lte=34).count()
        edad_mayor_35 = partos_tipo.filter(madre__edad__gt=35).count()
        
        rn_menor_2_5 = partos_tipo.filter(recien_nacidos__peso__lt=2.5).count()
        rn_mayor_2_5 = partos_tipo.filter(recien_nacidos__peso__gte=2.5).count()
        
        data.append([
            f"Parto {tipo}",
            str(count),
            str(edad_menores_15),
            str(edad_15_19),
            str(edad_20_34),
            str(edad_mayor_35),
            str(rn_menor_2_5),
            str(rn_mayor_2_5)
        ])
    
    table = Table(data, colWidths=[1.5*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch, 0.6*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    # PARTOS PREMATUROS
    data_prematuros = [['Partos Prematuros', 'Total']]
    data_prematuros.append(['<24 semanas', str(partos.filter(edad_gestacional_semanas__lt=24).count())])
    data_prematuros.append(['24-28 semanas', str(partos.filter(edad_gestacional_semanas__gte=24, edad_gestacional_semanas__lte=28).count())])
    data_prematuros.append(['29-32 semanas', str(partos.filter(edad_gestacional_semanas__gte=29, edad_gestacional_semanas__lte=32).count())])
    data_prematuros.append(['33-36 semanas', str(partos.filter(edad_gestacional_semanas__gte=33, edad_gestacional_semanas__lte=36).count())])
    
    table_prematuros = Table(data_prematuros, colWidths=[2.5*inch, 1*inch])
    table_prematuros.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_prematuros)
    elements.append(Spacer(1, 0.2*inch))
    
    # CONTACTO INMEDIATO PIEL A PIEL
    data_apego = [['Contacto Inmediato Piel a Piel', 'Total']]
    rn_apego_menor = RecienNacido.objects.filter(parto__in=partos, apego_piel_a_piel=True, peso__lt=2.5).count()
    rn_apego_mayor = RecienNacido.objects.filter(parto__in=partos, apego_piel_a_piel=True, peso__gte=2.5).count()
    data_apego.append(['RN <2.5kg con apego', str(rn_apego_menor)])
    data_apego.append(['RN ≥2.5kg con apego', str(rn_apego_mayor)])
    
    table_apego = Table(data_apego, colWidths=[2.5*inch, 1*inch])
    table_apego.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_apego)
    elements.append(Spacer(1, 0.2*inch))
    
    # LACTANCIA MATERNA ANTES DE 1 HORA
    data_lactancia = [['Lactancia Materna Antes de 1 Hora', 'Total']]
    rn_lactancia_menor = RecienNacido.objects.filter(parto__in=partos, lactancia_precoz=True, peso__lt=2.5).count()
    rn_lactancia_mayor = RecienNacido.objects.filter(parto__in=partos, lactancia_precoz=True, peso__gte=2.5).count()
    data_lactancia.append(['RN <2.5kg con lactancia', str(rn_lactancia_menor)])
    data_lactancia.append(['RN ≥2.5kg con lactancia', str(rn_lactancia_mayor)])
    
    table_lactancia = Table(data_lactancia, colWidths=[2.5*inch, 1*inch])
    table_lactancia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_lactancia)
    elements.append(Spacer(1, 0.2*inch))
    
    # NACIONALIDAD DE LA MADRE
    data_nacionalidad = [['Nacionalidad de la Madre', 'Total']]
    madres_chilenas = partos.filter(madre__nacionalidad='Chilena').count()
    madres_extranjeras = partos.exclude(madre__nacionalidad='Chilena').count()
    data_nacionalidad.append(['Madre Chilena', str(madres_chilenas)])
    data_nacionalidad.append(['Madre Extranjera', str(madres_extranjeras)])
    
    table_nacionalidad = Table(data_nacionalidad, colWidths=[2.5*inch, 1*inch])
    table_nacionalidad.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_nacionalidad)
    elements.append(Spacer(1, 0.2*inch))
    
    # CON ACOMPAÑANTE
    data_acompanante = [['Con Acompañante', 'Total']]
    partos_con_acompanante = partos.exclude(acompanante__isnull=True).exclude(acompanante__exact='').count()
    data_acompanante.append(['Partos con Acompañante', str(partos_con_acompanante)])
    
    table_acompanante = Table(data_acompanante, colWidths=[2.5*inch, 1*inch])
    table_acompanante.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_acompanante)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_pdf_seccion_b(fecha_inicio, fecha_fin):
    """
    Exporta Sección B: Interrupción del Embarazo (REM) a PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    elements.append(Paragraph("SECCIÓN B: INTERRUPCIÓN DEL EMBARAZO", title_style))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    abortos = Aborto.objects.filter(fecha_derivacion__date__range=[fecha_inicio, fecha_fin])
    total_abortos = abortos.count()
    
    data = [['Característica', 'Total', 'Menor 15', '15-19', '20-34', 'Mayor 35']]
    data.append(['Total de Interrupciones', str(total_abortos), '', '', '', ''])
    
    causales = abortos.values('causal').annotate(count=Count('id')).order_by('causal')
    for causal_item in causales:
        causal = causal_item['causal'] or 'Sin especificar'
        count = causal_item['count']
        
        abortos_causal = abortos.filter(causal=causal_item['causal'] if causal_item['causal'] else None)
        
        edad_menores_15 = abortos_causal.filter(madre__edad__lt=15).count()
        edad_15_19 = abortos_causal.filter(madre__edad__gte=15, madre__edad__lte=19).count()
        edad_20_34 = abortos_causal.filter(madre__edad__gte=20, madre__edad__lte=34).count()
        edad_mayor_35 = abortos_causal.filter(madre__edad__gt=35).count()
        
        data.append([
            f"{causal}",
            str(count),
            str(edad_menores_15),
            str(edad_15_19),
            str(edad_20_34),
            str(edad_mayor_35)
        ])
    
    table = Table(data, colWidths=[2.5*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.2*inch))
    
    # DETALLE DE CAUSALES
    data_causales_detalle = [['Detalle de Causales', 'Total']]
    causales_dict = {
        'na': 'No Aplica (Espontáneo)',
        'causal_1': 'Causal 1: Riesgo vital materno',
        'causal_2': 'Causal 2: Inviabilidad fetal',
        'causal_3': 'Causal 3: Violación',
    }
    
    for causal_code, causal_label in causales_dict.items():
        count = abortos.filter(causal=causal_code).count()
        data_causales_detalle.append([causal_label, str(count)])
    
    table_causales_detalle = Table(data_causales_detalle, colWidths=[3.5*inch, 1*inch])
    table_causales_detalle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_causales_detalle)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_pdf_seccion_c(fecha_inicio, fecha_fin):
    """
    Exporta Sección C: Métodos Anticonceptivos al Alta (REM) a PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    elements.append(Paragraph("SECCIÓN C: MÉTODOS ANTICONCEPTIVOS AL ALTA", title_style))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    altas = Alta.objects.filter(madre__isnull=False, fecha_creacion__date__range=[fecha_inicio, fecha_fin])
    total_altas = altas.count()
    
    # RESUMEN
    altas_con_anticonceptivo = altas.exclude(metodo_anticonceptivo='ninguno').exclude(metodo_anticonceptivo__isnull=True).count()
    cobertura = (altas_con_anticonceptivo / total_altas * 100) if total_altas > 0 else 0
    
    data_resumen = [['Concepto', 'Valor']]
    data_resumen.append(['Total de Altas de Madre', str(total_altas)])
    data_resumen.append(['Altas con Anticonceptivo', str(altas_con_anticonceptivo)])
    data_resumen.append(['Cobertura (%)', f'{cobertura:.2f}%'])
    
    table_resumen = Table(data_resumen, colWidths=[2.5*inch, 1.5*inch])
    table_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_resumen)
    elements.append(Spacer(1, 0.2*inch))
    
    # MÉTODOS ENTREGADOS
    data_metodos = [['Método', 'Cantidad', 'Porcentaje']]
    
    metodos = altas.exclude(metodo_anticonceptivo='ninguno').exclude(metodo_anticonceptivo__isnull=True).values('metodo_anticonceptivo').annotate(count=Count('id')).order_by('-count')
    for metodo_item in metodos:
        metodo = metodo_item['metodo_anticonceptivo'] or 'Sin especificar'
        count = metodo_item['count']
        porcentaje = (count / altas_con_anticonceptivo * 100) if altas_con_anticonceptivo > 0 else 0
        
        data_metodos.append([
            f"{metodo}",
            str(count),
            f'{porcentaje:.2f}%'
        ])
    
    table_metodos = Table(data_metodos, colWidths=[2.5*inch, 1*inch, 1*inch])
    table_metodos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(Paragraph("MÉTODOS ENTREGADOS", ParagraphStyle(
        'MethodsTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )))
    elements.append(table_metodos)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_pdf_seccion_d(fecha_inicio, fecha_fin):
    """
    Exporta Sección D: Información de Recién Nacidos (REM) a PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    elements.append(Paragraph("SECCIÓN D: INFORMACIÓN DE RECIÉN NACIDOS", title_style))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    recien_nacidos = RecienNacido.objects.filter(fecha_registro__date__range=[fecha_inicio, fecha_fin])
    total_rn = recien_nacidos.count()
    
    # TOTAL DE RN
    data_resumen = [['Concepto', 'Cantidad']]
    data_resumen.append(['Total de RN', str(total_rn)])
    
    table_resumen = Table(data_resumen, colWidths=[2.5*inch, 1.5*inch])
    table_resumen.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_resumen)
    elements.append(Spacer(1, 0.2*inch))
    
    # POR SEXO
    data_sexo = [['Por Sexo', 'Total']]
    masculino = recien_nacidos.filter(sexo='M').count()
    femenino = recien_nacidos.filter(sexo='F').count()
    data_sexo.append(['Masculino', str(masculino)])
    data_sexo.append(['Femenino', str(femenino)])
    
    table_sexo = Table(data_sexo, colWidths=[2.5*inch, 1.5*inch])
    table_sexo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_sexo)
    elements.append(Spacer(1, 0.2*inch))
    
    # APGAR (1 minuto)
    data_apgar = [['APGAR (1 minuto)', 'Total']]
    apgar_menor_7 = recien_nacidos.filter(apgar_1_min__lt=7).count()
    apgar_mayor_7 = recien_nacidos.filter(apgar_1_min__gte=7).count()
    data_apgar.append(['APGAR < 7', str(apgar_menor_7)])
    data_apgar.append(['APGAR ≥ 7', str(apgar_mayor_7)])
    
    table_apgar = Table(data_apgar, colWidths=[2.5*inch, 1.5*inch])
    table_apgar.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_apgar)
    elements.append(Spacer(1, 0.2*inch))
    
    # POR PESO
    data_peso = [['Por Peso', 'Total']]
    bajo_peso = recien_nacidos.filter(peso__lt=2.5).count()
    peso_normal = recien_nacidos.filter(peso__gte=2.5, peso__lt=4.0).count()
    macrosomia = recien_nacidos.filter(peso__gte=4.0).count()
    data_peso.append(['Bajo Peso (<2.5kg)', str(bajo_peso)])
    data_peso.append(['Peso Normal (2.5-3.9kg)', str(peso_normal)])
    data_peso.append(['Macrosomía (≥4.0kg)', str(macrosomia)])
    
    table_peso = Table(data_peso, colWidths=[2.5*inch, 1.5*inch])
    table_peso.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_peso)
    elements.append(Spacer(1, 0.2*inch))
    
    # POR TALLA
    data_talla = [['Por Talla', 'Valor (cm)']]
    talla_promedio = recien_nacidos.exclude(talla__isnull=True).aggregate(avg=Avg('talla'))['avg']
    if talla_promedio:
        data_talla.append(['Talla Promedio', f'{talla_promedio:.2f}'])
    else:
        data_talla.append(['Talla Promedio', 'S/D'])
    
    table_talla = Table(data_talla, colWidths=[2.5*inch, 1.5*inch])
    table_talla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_talla)
    elements.append(Spacer(1, 0.2*inch))
    
    # LACTANCIA PRECOZ
    data_lactancia = [['Lactancia Precoz', 'Total']]
    lactancia_si = recien_nacidos.filter(lactancia_precoz=True).count()
    data_lactancia.append(['RN con Lactancia Precoz', str(lactancia_si)])
    
    table_lactancia = Table(data_lactancia, colWidths=[2.5*inch, 1.5*inch])
    table_lactancia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_lactancia)
    elements.append(Spacer(1, 0.2*inch))
    
    # APEGO PIEL A PIEL
    data_apego = [['Apego Piel a Piel', 'Total']]
    apego_si = recien_nacidos.filter(apego_piel_a_piel=True).count()
    data_apego.append(['RN con Apego Piel a Piel', str(apego_si)])
    
    table_apego = Table(data_apego, colWidths=[2.5*inch, 1.5*inch])
    table_apego.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    elements.append(table_apego)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def crear_pdf_export_madres(fecha_inicio, fecha_fin):
    """
    Exporta PDF completo: Madres+Partos+Secciones A-D
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # ===== PÁGINA 1: RESUMEN GENERAL =====
    elements.append(Paragraph("EXPORTACIÓN COMPLETA: MADRES, PARTOS Y REM", title_style))
    elements.append(Paragraph(f"Período: {fecha_inicio} a {fecha_fin}", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Resumen general
    madres = Madre.objects.filter(fecha_ingreso__date__range=[fecha_inicio, fecha_fin])
    partos = Parto.objects.filter(fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin])
    rn = RecienNacido.objects.filter(parto__fecha_hora_inicio__date__range=[fecha_inicio, fecha_fin])
    
    data = [['Concepto', 'Cantidad']]
    data.append(['Total Madres', str(madres.count())])
    data.append(['Total Partos', str(partos.count())])
    data.append(['Total Recién Nacidos', str(rn.count())])
    
    table = Table(data, colWidths=[3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(table)
    elements.append(PageBreak())
    
    # ===== SECCIÓN A: INFORMACIÓN GENERAL DE PARTOS =====
    elements.append(Paragraph("SECCIÓN A: INFORMACIÓN GENERAL DE PARTOS", section_title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    total_partos = partos.count()
    data_a = [['Característica', 'Total', 'Menor 15', '15-19', '20-34', 'Mayor 35', 'RN <2.5kg', 'RN ≥2.5kg']]
    data_a.append(['Total de Partos', str(total_partos), '', '', '', '', '', ''])
    
    tipos_partos = partos.values('tipo').annotate(count=Count('id')).order_by('tipo')
    for tipo_parto in tipos_partos:
        tipo = tipo_parto['tipo'] or 'Sin especificar'
        count = tipo_parto['count']
        
        partos_tipo = partos.filter(tipo=tipo_parto['tipo'] if tipo_parto['tipo'] else None)
        
        edad_menores_15 = partos_tipo.filter(madre__edad__lt=15).count()
        edad_15_19 = partos_tipo.filter(madre__edad__gte=15, madre__edad__lte=19).count()
        edad_20_34 = partos_tipo.filter(madre__edad__gte=20, madre__edad__lte=34).count()
        edad_mayor_35 = partos_tipo.filter(madre__edad__gt=35).count()
        
        rn_menor_2_5 = partos_tipo.filter(recien_nacidos__peso__lt=2.5).count()
        rn_mayor_2_5 = partos_tipo.filter(recien_nacidos__peso__gte=2.5).count()
        
        data_a.append([
            f"Parto {tipo}",
            str(count),
            str(edad_menores_15),
            str(edad_15_19),
            str(edad_20_34),
            str(edad_mayor_35),
            str(rn_menor_2_5),
            str(rn_mayor_2_5)
        ])
    
    table_a = Table(data_a, colWidths=[1.2*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch])
    table_a.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(table_a)
    elements.append(Spacer(1, 0.15*inch))
    
    # PARTOS PREMATUROS
    data_prematuros = [['Partos Prematuros', 'Total']]
    data_prematuros.append(['<24 semanas', str(partos.filter(edad_gestacional_semanas__lt=24).count())])
    data_prematuros.append(['24-28 semanas', str(partos.filter(edad_gestacional_semanas__gte=24, edad_gestacional_semanas__lte=28).count())])
    data_prematuros.append(['29-32 semanas', str(partos.filter(edad_gestacional_semanas__gte=29, edad_gestacional_semanas__lte=32).count())])
    data_prematuros.append(['33-36 semanas', str(partos.filter(edad_gestacional_semanas__gte=33, edad_gestacional_semanas__lte=36).count())])
    
    table_prematuros = Table(data_prematuros, colWidths=[2.5*inch, 1*inch])
    table_prematuros.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_prematuros)
    elements.append(Spacer(1, 0.15*inch))
    
    # CONTACTO INMEDIATO PIEL A PIEL
    data_apego = [['Contacto Inmediato Piel a Piel', 'Total']]
    rn_apego_menor = RecienNacido.objects.filter(parto__in=partos, apego_piel_a_piel=True, peso__lt=2.5).count()
    rn_apego_mayor = RecienNacido.objects.filter(parto__in=partos, apego_piel_a_piel=True, peso__gte=2.5).count()
    data_apego.append(['RN <2.5kg con apego', str(rn_apego_menor)])
    data_apego.append(['RN ≥2.5kg con apego', str(rn_apego_mayor)])
    
    table_apego = Table(data_apego, colWidths=[2.5*inch, 1*inch])
    table_apego.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_apego)
    elements.append(Spacer(1, 0.15*inch))
    
    # LACTANCIA MATERNA ANTES DE 1 HORA
    data_lactancia = [['Lactancia Materna Antes de 1 Hora', 'Total']]
    rn_lactancia_menor = RecienNacido.objects.filter(parto__in=partos, lactancia_precoz=True, peso__lt=2.5).count()
    rn_lactancia_mayor = RecienNacido.objects.filter(parto__in=partos, lactancia_precoz=True, peso__gte=2.5).count()
    data_lactancia.append(['RN <2.5kg con lactancia', str(rn_lactancia_menor)])
    data_lactancia.append(['RN ≥2.5kg con lactancia', str(rn_lactancia_mayor)])
    
    table_lactancia = Table(data_lactancia, colWidths=[2.5*inch, 1*inch])
    table_lactancia.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_lactancia)
    elements.append(Spacer(1, 0.15*inch))
    
    # NACIONALIDAD DE LA MADRE
    data_nacionalidad = [['Nacionalidad de la Madre', 'Total']]
    madres_chilenas = partos.filter(madre__nacionalidad='Chilena').count()
    madres_extranjeras = partos.exclude(madre__nacionalidad='Chilena').count()
    data_nacionalidad.append(['Madre Chilena', str(madres_chilenas)])
    data_nacionalidad.append(['Madre Extranjera', str(madres_extranjeras)])
    
    table_nacionalidad = Table(data_nacionalidad, colWidths=[2.5*inch, 1*inch])
    table_nacionalidad.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_nacionalidad)
    elements.append(Spacer(1, 0.15*inch))
    
    # CON ACOMPAÑANTE
    data_acompanante = [['Con Acompañante', 'Total']]
    partos_con_acompanante = partos.exclude(acompanante__isnull=True).exclude(acompanante__exact='').count()
    data_acompanante.append(['Partos con Acompañante', str(partos_con_acompanante)])
    
    table_acompanante = Table(data_acompanante, colWidths=[2.5*inch, 1*inch])
    table_acompanante.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_acompanante)
    elements.append(PageBreak())
    
    # ===== SECCIÓN B: INTERRUPCIÓN DEL EMBARAZO =====
    elements.append(Paragraph("SECCIÓN B: INTERRUPCIÓN DEL EMBARAZO", section_title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    abortos = Aborto.objects.filter(fecha_derivacion__date__range=[fecha_inicio, fecha_fin])
    total_abortos = abortos.count()
    
    data_b = [['Característica', 'Total', 'Menor 15', '15-19', '20-34', 'Mayor 35']]
    data_b.append(['Total de Interrupciones', str(total_abortos), '', '', '', ''])
    
    causales = abortos.values('causal').annotate(count=Count('id')).order_by('causal')
    for causal_item in causales:
        causal = causal_item['causal'] or 'Sin especificar'
        count = causal_item['count']
        
        abortos_causal = abortos.filter(causal=causal_item['causal'] if causal_item['causal'] else None)
        
        edad_menores_15 = abortos_causal.filter(madre__edad__lt=15).count()
        edad_15_19 = abortos_causal.filter(madre__edad__gte=15, madre__edad__lte=19).count()
        edad_20_34 = abortos_causal.filter(madre__edad__gte=20, madre__edad__lte=34).count()
        edad_mayor_35 = abortos_causal.filter(madre__edad__gt=35).count()
        
        data_b.append([
            f"{causal}",
            str(count),
            str(edad_menores_15),
            str(edad_15_19),
            str(edad_20_34),
            str(edad_mayor_35)
        ])
    
    table_b = Table(data_b, colWidths=[2*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch])
    table_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    elements.append(table_b)
    elements.append(Spacer(1, 0.15*inch))
    
    # DETALLE DE CAUSALES
    data_causales_detalle = [['Detalle de Causales', 'Total']]
    causales_dict = {
        'na': 'No Aplica (Espontáneo)',
        'causal_1': 'Causal 1: Riesgo vital materno',
        'causal_2': 'Causal 2: Inviabilidad fetal',
        'causal_3': 'Causal 3: Violación',
    }
    
    for causal_code, causal_label in causales_dict.items():
        count = abortos.filter(causal=causal_code).count()
        data_causales_detalle.append([causal_label, str(count)])
    
    table_causales_detalle = Table(data_causales_detalle, colWidths=[3.5*inch, 1*inch])
    table_causales_detalle.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_causales_detalle)
    elements.append(PageBreak())
    
    # ===== SECCIÓN C: MÉTODOS ANTICONCEPTIVOS AL ALTA =====
    elements.append(Paragraph("SECCIÓN C: MÉTODOS ANTICONCEPTIVOS AL ALTA", section_title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    altas = Alta.objects.filter(madre__isnull=False, fecha_creacion__date__range=[fecha_inicio, fecha_fin])
    total_altas = altas.count()
    
    # RESUMEN
    altas_con_anticonceptivo = altas.exclude(metodo_anticonceptivo='ninguno').exclude(metodo_anticonceptivo__isnull=True).count()
    cobertura = (altas_con_anticonceptivo / total_altas * 100) if total_altas > 0 else 0
    
    data_resumen_c = [['Concepto', 'Valor']]
    data_resumen_c.append(['Total de Altas de Madre', str(total_altas)])
    data_resumen_c.append(['Altas con Anticonceptivo', str(altas_con_anticonceptivo)])
    data_resumen_c.append(['Cobertura (%)', f'{cobertura:.2f}%'])
    
    table_resumen_c = Table(data_resumen_c, colWidths=[2.5*inch, 1.2*inch])
    table_resumen_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_resumen_c)
    elements.append(Spacer(1, 0.15*inch))
    
    # MÉTODOS ENTREGADOS
    data_metodos_c = [['Método', 'Cantidad', 'Porcentaje']]
    
    metodos = altas.exclude(metodo_anticonceptivo='ninguno').exclude(metodo_anticonceptivo__isnull=True).values('metodo_anticonceptivo').annotate(count=Count('id')).order_by('-count')
    for metodo_item in metodos:
        metodo = metodo_item['metodo_anticonceptivo'] or 'Sin especificar'
        count = metodo_item['count']
        porcentaje = (count / altas_con_anticonceptivo * 100) if altas_con_anticonceptivo > 0 else 0
        
        data_metodos_c.append([
            f"{metodo}",
            str(count),
            f'{porcentaje:.2f}%'
        ])
    
    table_metodos_c = Table(data_metodos_c, colWidths=[2.5*inch, 0.9*inch, 0.9*inch])
    table_metodos_c.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')])
    ]))
    
    elements.append(Paragraph("MÉTODOS ENTREGADOS", ParagraphStyle(
        'MethodsTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#0070C0'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )))
    elements.append(table_metodos_c)
    elements.append(PageBreak())
    
    # ===== SECCIÓN D: INFORMACIÓN DE RECIÉN NACIDOS =====
    elements.append(Paragraph("SECCIÓN D: INFORMACIÓN DE RECIÉN NACIDOS", section_title_style))
    elements.append(Spacer(1, 0.15*inch))
    
    recien_nacidos = RecienNacido.objects.filter(fecha_registro__date__range=[fecha_inicio, fecha_fin])
    total_rn = recien_nacidos.count()
    
    # TOTAL DE RN
    data_resumen_d = [['Concepto', 'Cantidad']]
    data_resumen_d.append(['Total de RN', str(total_rn)])
    
    table_resumen_d = Table(data_resumen_d, colWidths=[2.5*inch, 1.2*inch])
    table_resumen_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_resumen_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # POR SEXO
    data_sexo_d = [['Por Sexo', 'Total']]
    masculino_d = recien_nacidos.filter(sexo='M').count()
    femenino_d = recien_nacidos.filter(sexo='F').count()
    data_sexo_d.append(['Masculino', str(masculino_d)])
    data_sexo_d.append(['Femenino', str(femenino_d)])
    
    table_sexo_d = Table(data_sexo_d, colWidths=[2.5*inch, 1.2*inch])
    table_sexo_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_sexo_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # APGAR (1 minuto)
    data_apgar_d = [['APGAR (1 minuto)', 'Total']]
    apgar_menor_7_d = recien_nacidos.filter(apgar_1_min__lt=7).count()
    apgar_mayor_7_d = recien_nacidos.filter(apgar_1_min__gte=7).count()
    data_apgar_d.append(['APGAR < 7', str(apgar_menor_7_d)])
    data_apgar_d.append(['APGAR ≥ 7', str(apgar_mayor_7_d)])
    
    table_apgar_d = Table(data_apgar_d, colWidths=[2.5*inch, 1.2*inch])
    table_apgar_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_apgar_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # POR PESO
    data_peso_d = [['Por Peso', 'Total']]
    bajo_peso_d = recien_nacidos.filter(peso__lt=2.5).count()
    peso_normal_d = recien_nacidos.filter(peso__gte=2.5, peso__lt=4.0).count()
    macrosomia_d = recien_nacidos.filter(peso__gte=4.0).count()
    data_peso_d.append(['Bajo Peso (<2.5kg)', str(bajo_peso_d)])
    data_peso_d.append(['Peso Normal (2.5-3.9kg)', str(peso_normal_d)])
    data_peso_d.append(['Macrosomía (≥4.0kg)', str(macrosomia_d)])
    
    table_peso_d = Table(data_peso_d, colWidths=[2.5*inch, 1.2*inch])
    table_peso_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_peso_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # POR TALLA
    data_talla_d = [['Por Talla', 'Valor (cm)']]
    talla_promedio_d = recien_nacidos.exclude(talla__isnull=True).aggregate(avg=Avg('talla'))['avg']
    if talla_promedio_d:
        data_talla_d.append(['Talla Promedio', f'{talla_promedio_d:.2f}'])
    else:
        data_talla_d.append(['Talla Promedio', 'S/D'])
    
    table_talla_d = Table(data_talla_d, colWidths=[2.5*inch, 1.2*inch])
    table_talla_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_talla_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # LACTANCIA PRECOZ
    data_lactancia_d = [['Lactancia Precoz', 'Total']]
    lactancia_si_d = recien_nacidos.filter(lactancia_precoz=True).count()
    data_lactancia_d.append(['RN con Lactancia Precoz', str(lactancia_si_d)])
    
    table_lactancia_d = Table(data_lactancia_d, colWidths=[2.5*inch, 1.2*inch])
    table_lactancia_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_lactancia_d)
    elements.append(Spacer(1, 0.15*inch))
    
    # APEGO PIEL A PIEL
    data_apego_d = [['Apego Piel a Piel', 'Total']]
    apego_si_d = recien_nacidos.filter(apego_piel_a_piel=True).count()
    data_apego_d.append(['RN con Apego Piel a Piel', str(apego_si_d)])
    
    table_apego_d = Table(data_apego_d, colWidths=[2.5*inch, 1.2*inch])
    table_apego_d.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070C0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
    ]))
    elements.append(table_apego_d)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def descargar_pdf_response(pdf_buffer, nombre):
    """
    Retorna un HttpResponse con el PDF para descargar
    """
    response = HttpResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return response
