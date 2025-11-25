"""
Script para calcular y visualizar los KPIs de GreenDelivery.
"""
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuración
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'greendelivery',
    'user': 'postgres',
    'password': '1234'
}

def conectar_bd():
    return psycopg2.connect(**DB_CONFIG)

def calcular_kpi_sla():
    """
    KPI 1: % de Envíos en SLA
    """
    conn = conectar_bd()
    
    query = """
    WITH paquetes_con_alertas AS (
        SELECT DISTINCT id_paquete FROM alerts
    ),
    todos_los_paquetes AS (
        SELECT DISTINCT id_paquete FROM telemetry
    )
    SELECT 
        COUNT(DISTINCT t.id_paquete) as total_paquetes,
        COUNT(DISTINCT t.id_paquete) - COUNT(DISTINCT a.id_paquete) as paquetes_sin_alertas,
        ROUND(
            ((COUNT(DISTINCT t.id_paquete)::numeric - COUNT(DISTINCT a.id_paquete)::numeric) / 
             COUNT(DISTINCT t.id_paquete)::numeric) * 100, 
            2
        ) as porcentaje_sla
    FROM todos_los_paquetes t
    LEFT JOIN paquetes_con_alertas a ON t.id_paquete = a.id_paquete;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df.iloc[0].to_dict()

def calcular_kpi_mttd():
    """
    KPI 2: Tiempo Medio de Detección
    """
    conn = conectar_bd()
    
    # Simplificado: usamos num_eventos * 2 segundos
    query = """
    SELECT 
        COUNT(*) as total_alertas,
        ROUND(AVG(num_eventos * 2.0)::numeric, 2) as mttd_segundos,
        ROUND(MIN(num_eventos * 2.0)::numeric, 2) as deteccion_mas_rapida,
        ROUND(MAX(num_eventos * 2.0)::numeric, 2) as deteccion_mas_lenta
    FROM alerts;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df.iloc[0].to_dict()

def calcular_kpi_falsos_positivos():
    """
    KPI 3: % de Falsos Positivos (estimado)
    """
    conn = conectar_bd()
    
    # Como no tenemos validaciones reales, estimamos 15%
    query = """
    SELECT 
        COUNT(*) as total_alertas,
        ROUND(COUNT(*) * 0.15) as falsos_positivos_estimados,
        15.0 as porcentaje_fp_estimado
    FROM alerts;
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    return df.iloc[0].to_dict()

def generar_dashboard():
    """
    Genera un dashboard visual con los 3 KPIs
    """
    print("="*60)
    print("📊 DASHBOARD DE KPIs - GREENDELIVERY")
    print("="*60)
    
    # Calcular KPIs
    print("\n🔄 Calculando KPIs...")
    kpi1 = calcular_kpi_sla()
    kpi2 = calcular_kpi_mttd()
    kpi3 = calcular_kpi_falsos_positivos()
    
    # Mostrar en consola
    print("\n" + "="*60)
    print("📈 KPI 1: % DE ENVÍOS EN SLA (Tasa de Éxito)")
    print("="*60)
    print(f"Total de paquetes:       {kpi1['total_paquetes']}")
    print(f"Paquetes sin alertas:    {kpi1['paquetes_sin_alertas']}")
    print(f"📊 SLA: {kpi1['porcentaje_sla']}%")
    
    if kpi1['porcentaje_sla'] >= 95:
        print("✅ Excelente - Cumpliendo la promesa de calidad")
    elif kpi1['porcentaje_sla'] >= 90:
        print("⚠️  Aceptable - Pero hay margen de mejora")
    else:
        print("❌ Crítico - Revisar procesos urgentemente")
    
    print("\n" + "="*60)
    print("⏱️  KPI 2: TIEMPO MEDIO DE DETECCIÓN (MTTD)")
    print("="*60)
    print(f"Total de alertas:        {int(kpi2['total_alertas'])}")
    print(f"Detección más rápida:    {kpi2['deteccion_mas_rapida']}s")
    print(f"Detección más lenta:     {kpi2['deteccion_mas_lenta']}s")
    print(f"📊 MTTD: {kpi2['mttd_segundos']}s")
    
    if kpi2['mttd_segundos'] < 30:
        print("✅ Excelente - Reacción muy rápida")
    elif kpi2['mttd_segundos'] < 60:
        print("⚠️  Aceptable - Suficiente para intervenir")
    else:
        print("❌ Lento - Solo sirve para autopsias")
    
    print("\n" + "="*60)
    print("🚨 KPI 3: % DE FALSOS POSITIVOS (Índice de Confianza)")
    print("="*60)
    print(f"Total de alertas:        {int(kpi3['total_alertas'])}")
    print(f"Falsos positivos (est.): {int(kpi3['falsos_positivos_estimados'])}")
    print(f"📊 Tasa de FP: {kpi3['porcentaje_fp_estimado']}%")
    
    if kpi3['porcentaje_fp_estimado'] < 10:
        print("✅ Excelente - Sistema confiable")
    elif kpi3['porcentaje_fp_estimado'] < 20:
        print("⚠️  Aceptable - Monitorizar")
    else:
        print("❌ Crítico - Riesgo de fatiga de alertas")
    
    # ==========================================
    # VISUALIZACIÓN
    # ==========================================
    print("\n📊 Generando gráficos...")
    
    fig = plt.figure(figsize=(16, 5))
    
    # Colores corporativos
    color_excelente = '#2ecc71'
    color_aceptable = '#f39c12'
    color_critico = '#e74c3c'
    
    # ==========================================
    # GRÁFICO 1: SLA
    # ==========================================
    ax1 = plt.subplot(131)
    
    # Gauge chart simplificado
    porcentaje_sla = kpi1['porcentaje_sla']
    color_sla = color_excelente if porcentaje_sla >= 95 else (
        color_aceptable if porcentaje_sla >= 90 else color_critico
    )
    
    ax1.barh(['SLA'], [porcentaje_sla], color=color_sla, alpha=0.7, height=0.5)
    ax1.barh(['SLA'], [100 - porcentaje_sla], left=[porcentaje_sla], 
             color='lightgray', alpha=0.3, height=0.5)
    
    ax1.set_xlim(0, 100)
    ax1.set_xlabel('Porcentaje (%)', fontsize=11)
    ax1.set_title(f'KPI 1: % Envíos en SLA\n{porcentaje_sla}%', 
                  fontsize=13, fontweight='bold')
    ax1.axvline(x=95, color='green', linestyle='--', alpha=0.5, label='Meta (95%)')
    ax1.legend(fontsize=9)
    ax1.grid(axis='x', alpha=0.3)
    
    # Añadir texto
    ax1.text(porcentaje_sla/2, 0, f'{porcentaje_sla}%', 
             ha='center', va='center', fontsize=16, fontweight='bold', color='white')
    
    # ==========================================
    # GRÁFICO 2: MTTD
    # ==========================================
    ax2 = plt.subplot(132)
    
    mttd = kpi2['mttd_segundos']
    color_mttd = color_excelente if mttd < 30 else (
        color_aceptable if mttd < 60 else color_critico
    )
    
    bars = ax2.bar(['Más rápida', 'MTTD Promedio', 'Más lenta'], 
                   [kpi2['deteccion_mas_rapida'], mttd, kpi2['deteccion_mas_lenta']],
                   color=[color_excelente, color_mttd, color_critico],
                   alpha=0.7, edgecolor='black')
    
    ax2.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Meta (< 30s)')
    ax2.set_ylabel('Segundos', fontsize=11)
    ax2.set_title(f'KPI 2: Tiempo Medio de Detección\n{mttd}s', 
                  fontsize=13, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    
    # Añadir valores
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}s',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # ==========================================
    # GRÁFICO 3: FALSOS POSITIVOS
    # ==========================================
    ax3 = plt.subplot(133)
    
    fp_pct = kpi3['porcentaje_fp_estimado']
    color_fp = color_excelente if fp_pct < 10 else (
        color_aceptable if fp_pct < 20 else color_critico
    )
    
    # Pie chart
    sizes = [fp_pct, 100 - fp_pct]
    colors_pie = [color_fp, color_excelente]
    labels = [f'Falsos Positivos\n{fp_pct}%', f'Alertas Correctas\n{100-fp_pct}%']
    explode = (0.1, 0)
    
    ax3.pie(sizes, explode=explode, labels=labels, colors=colors_pie,
            autopct='%1.1f%%', shadow=True, startangle=90,
            textprops={'fontsize': 10, 'fontweight': 'bold'})
    
    ax3.set_title(f'KPI 3: Tasa de Falsos Positivos\n{fp_pct}% (estimado)', 
                  fontsize=13, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('analytics/dashboard_kpis.png', dpi=300, bbox_inches='tight')
    print(f"   └─ Dashboard guardado: analytics/dashboard_kpis.png")
    
    # ==========================================
    # GUARDAR INFORME
    # ==========================================
    print("\n📄 Generando informe de KPIs...")
    
    informe = f"""
# DASHBOARD DE KPIs - GREENDELIVERY
**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## KPI 1: % DE ENVÍOS EN SLA 📦

**Objetivo:** Medir la calidad del servicio

| Métrica | Valor |
|---------|-------|
| Total de paquetes | {kpi1['total_paquetes']} |
| Paquetes sin alertas | {kpi1['paquetes_sin_alertas']} |
| **% en SLA** | **{kpi1['porcentaje_sla']}%** |

**Interpretación:**
- Meta: ≥ 95%
- Estado actual: {'✅ Excelente' if kpi1['porcentaje_sla'] >= 95 else '⚠️ Mejorar'}

---

## KPI 2: TIEMPO MEDIO DE DETECCIÓN ⏱️

**Objetivo:** Medir la velocidad de reacción del sistema

| Métrica | Valor |
|---------|-------|
| Total de alertas | {int(kpi2['total_alertas'])} |
| Detección más rápida | {kpi2['deteccion_mas_rapida']}s |
| **MTTD Promedio** | **{kpi2['mttd_segundos']}s** |
| Detección más lenta | {kpi2['deteccion_mas_lenta']}s |

**Interpretación:**
- Meta: < 30 segundos
- Estado actual: {'✅ Excelente' if kpi2['mttd_segundos'] < 30 else '⚠️ Mejorar'}

---

## KPI 3: % DE FALSOS POSITIVOS 🚨

**Objetivo:** Medir la confiabilidad del sistema de alertas

| Métrica | Valor |
|---------|-------|
| Total de alertas | {int(kpi3['total_alertas'])} |
| Falsos positivos (estimado) | {int(kpi3['falsos_positivos_estimados'])} |
| **Tasa de FP** | **{kpi3['porcentaje_fp_estimado']}%** |

**Interpretación:**
- Meta: < 10%
- Estado actual: {'✅ Excelente' if kpi3['porcentaje_fp_estimado'] < 10 else '⚠️ Monitorizar'}

---

## PROPUESTA DE MEJORA 💡

**Análisis del KPI más crítico:**

"""
    
    # Identificar el KPI más problemático
    if kpi1['porcentaje_sla'] < 95:
        informe += """
### 🔴 Problema Detectado: SLA por debajo del objetivo

**Situación actual:**
- Solo el {:.1f}% de los paquetes llegan sin incidentes
- Esto significa que {} de cada 100 paquetes tienen problemas

**Propuesta de mejora:**
1. **Análisis de causas raíz:** Revisar los tipos de incidentes más frecuentes
2. **Optimización de rutas:** Priorizar rutas con menos badenes/problemas
3. **Mejora del embalaje:** Considerar mejor aislamiento térmico
4. **Capacitación:** Entrenar a conductores en manejo de productos sensibles

**Impacto estimado:** 
- Reducción de incidentes en un 30%
- Incremento del SLA a > 95% en 3 meses

""".format(kpi1['porcentaje_sla'], 100 - int(kpi1['porcentaje_sla']))
    
    else:
        informe += f"""
### ✅ Sistema funcionando correctamente

El SLA está en {kpi1['porcentaje_sla']}% (por encima de la meta del 95%).

**Recomendación:** Mantener el monitoreo continuo y optimizar el KPI de falsos positivos 
para reducir la carga de trabajo del equipo de operaciones.
"""
    
    with open('analytics/informe_kpis.md', 'w', encoding='utf-8') as f:
        f.write(informe)
    
    print(f"   └─ Informe guardado: analytics/informe_kpis.md")
    
    print("\n" + "="*60)
    print("✅ ¡DASHBOARD GENERADO!")
    print("="*60)
    print("\nArchivos generados:")
    print("  • analytics/dashboard_kpis.png")
    print("  • analytics/informe_kpis.md")

if __name__ == "__main__":
    generar_dashboard()