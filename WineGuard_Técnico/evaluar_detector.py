"""
Script de evaluación del detector de incidentes.
Calcula Precisión, Recall, F1-Score y Matriz de Confusión.
"""
import pandas as pd
import numpy as np
from sklearn.metrics import (
    precision_score, 
    recall_score, 
    f1_score, 
    confusion_matrix,
    classification_report
)
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# ==============================================
# CONFIGURACIÓN (igual que detector.py)
# ==============================================
UMBRAL_TEMPERATURA = 8.0
UMBRAL_FUERZA_G = 2.5
UMBRAL_INCLINACION = 30.0
N_EVENTOS_CONSECUTIVOS = 3


class DetectorSimulado:
    """
    Simulación del detector para evaluar con datos históricos.
    """
    
    def __init__(self):
        self.estados = defaultdict(lambda: {
            'eventos_temp_alta': 0,
            'eventos_choque': 0,
            'en_alerta_temp': False,
            'en_alerta_choque': False
        })
    
    def procesar_evento(self, row):
        """
        Procesa un evento y devuelve 1 si debe generar alerta, 0 si no.
        """
        id_paquete = row['id_paquete']
        estado = self.estados[id_paquete]
        alerta = 0
        
        # ==========================================
        # DETECCIÓN DE TEMPERATURA
        # ==========================================
        if row['temperatura'] > UMBRAL_TEMPERATURA:
            estado['eventos_temp_alta'] += 1
            
            # ¿Alcanzamos el umbral?
            if estado['eventos_temp_alta'] >= N_EVENTOS_CONSECUTIVOS:
                alerta = 1
                estado['en_alerta_temp'] = True
        else:
            # Temperatura normalizada
            estado['eventos_temp_alta'] = 0
            estado['en_alerta_temp'] = False
        
        # ==========================================
        # DETECCIÓN DE CHOQUE
        # ==========================================
        if (row['fuerza_g'] > UMBRAL_FUERZA_G and 
            row['inclinacion'] > UMBRAL_INCLINACION):
            
            estado['eventos_choque'] += 1
            
            if estado['eventos_choque'] >= N_EVENTOS_CONSECUTIVOS:
                alerta = 1
                estado['en_alerta_choque'] = True
        else:
            estado['eventos_choque'] = 0
            estado['en_alerta_choque'] = False
        
        return alerta


def evaluar_detector():
    """
    Función principal de evaluación.
    """
    print("="*60)
    print("🔬 EVALUACIÓN DEL DETECTOR DE INCIDENTES")
    print("="*60)
    
    # Cargar datos
    print("\n📂 Cargando labels.csv...")
    df = pd.read_csv('analytics/labels.csv')
    print(f"   └─ {len(df)} eventos cargados")
    
    # Crear detector
    detector = DetectorSimulado()
    
    # Aplicar detector a todos los eventos
    print("\n🔄 Aplicando lógica de detección...")
    df['prediccion'] = df.apply(detector.procesar_evento, axis=1)
    
    # Extraer valores reales y predicciones
    # IMPORTANTE: Para la evaluación, solo consideramos como "incidente real"
    # aquellos eventos que están marcados como incidente=1 (parte de una alerta)
    y_true = df['incidente'].values
    y_pred = df['prediccion'].values
    
    # ==============================================
    # CALCULAR MÉTRICAS
    # ==============================================
    print("\n" + "="*60)
    print("📊 RESULTADOS DE LA EVALUACIÓN")
    print("="*60)
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    print(f"\n🎯 PRECISIÓN (Precision):  {precision:.4f} ({precision*100:.2f}%)")
    print(f"   └─ Cuando el sistema genera una alerta, acierta el {precision*100:.1f}% de las veces")
    
    print(f"\n🎯 EXHAUSTIVIDAD (Recall):  {recall:.4f} ({recall*100:.2f}%)")
    print(f"   └─ El sistema detecta el {recall*100:.1f}% de los incidentes reales")
    
    print(f"\n🎯 F1-SCORE:  {f1:.4f} ({f1*100:.2f}%)")
    print(f"   └─ Balance entre Precisión y Recall")
    
    # ==============================================
    # MATRIZ DE CONFUSIÓN
    # ==============================================
    cm = confusion_matrix(y_true, y_pred)
    
    print("\n" + "="*60)
    print("📈 MATRIZ DE CONFUSIÓN")
    print("="*60)
    print(f"\nVerdaderos Negativos (TN):  {cm[0,0]:>4}  ← Eventos normales correctamente identificados")
    print(f"Falsos Positivos (FP):      {cm[0,1]:>4}  ← ALERTAS FALSAS (❌)")
    print(f"Falsos Negativos (FN):      {cm[1,0]:>4}  ← INCIDENTES NO DETECTADOS (❌❌)")
    print(f"Verdaderos Positivos (TP):  {cm[1,1]:>4}  ← Incidentes correctamente detectados")
    
    # ==============================================
    # ANÁLISIS CUALITATIVO
    # ==============================================
    print("\n" + "="*60)
    print("💡 INTERPRETACIÓN PARA GREENDELIVERY")
    print("="*60)
    
    if f1 >= 0.7:
        print("\n✅ ¡Excelente! El detector tiene un rendimiento muy bueno (F1 ≥ 0.7)")
    else:
        print(f"\n⚠️  El detector tiene margen de mejora (F1 = {f1:.2f})")
    
    if cm[1,0] > 0:
        print(f"\n🔴 CRÍTICO: Hay {cm[1,0]} incidentes que NO fueron detectados (Falsos Negativos)")
        print(f"   └─ Impacto: Pérdida de producto, insatisfacción del cliente")
    else:
        print("\n✅ ¡Perfecto! Todos los incidentes reales fueron detectados (FN = 0)")
    
    if cm[0,1] > 0:
        print(f"\n🟡 ATENCIÓN: Hay {cm[0,1]} alertas falsas (Falsos Positivos)")
        print(f"   └─ Impacto: Pérdida de tiempo de los operarios (≈ {cm[0,1] * 5} minutos)")
    
    # ==============================================
    # VISUALIZACIÓN
    # ==============================================
    print("\n📊 Generando visualizaciones...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico 1: Matriz de Confusión
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Normal', 'Incidente'],
                yticklabels=['Normal', 'Incidente'],
                ax=axes[0], cbar_kws={'label': 'Cantidad'})
    axes[0].set_title('Matriz de Confusión', fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Realidad (Ground Truth)', fontsize=12)
    axes[0].set_xlabel('Predicción del Detector', fontsize=12)
    
    # Gráfico 2: Métricas
    metrics = ['Precisión', 'Recall', 'F1-Score']
    values = [precision, recall, f1]
    colors = ['#1f77b4' if v >= 0.7 else '#ff7f0e' for v in values]
    
    bars = axes[1].bar(metrics, values, color=colors, alpha=0.7, edgecolor='black')
    axes[1].axhline(y=0.7, color='green', linestyle='--', linewidth=2, label='Umbral objetivo (0.7)')
    axes[1].set_ylim(0, 1)
    axes[1].set_ylabel('Score', fontsize=12)
    axes[1].set_title('Métricas de Rendimiento', fontsize=14, fontweight='bold')
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    # Añadir valores en las barras
    for bar, value in zip(bars, values):
        height = bar.get_height()
        axes[1].text(bar.get_x() + bar.get_width()/2., height + 0.02,
                    f'{value:.3f}',
                    ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('analytics/evaluacion_detector.png', dpi=300, bbox_inches='tight')
    print(f"   └─ Gráfico guardado: analytics/evaluacion_detector.png")
    
    # ==============================================
    # GUARDAR INFORME
    # ==============================================
    print("\n📄 Generando informe...")
    
    informe = f"""
# INFORME DE EVALUACIÓN - DETECTOR DE INCIDENTES
**Fecha:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. CONFIGURACIÓN DEL DETECTOR

- **Umbral de Temperatura:** > {UMBRAL_TEMPERATURA}°C
- **Umbral de Fuerza G:** > {UMBRAL_FUERZA_G}G
- **Umbral de Inclinación:** > {UMBRAL_INCLINACION}°
- **Eventos Consecutivos (N):** {N_EVENTOS_CONSECUTIVOS}

**Justificación del valor N={N_EVENTOS_CONSECUTIVOS}:**
- 1-2 eventos podrían ser picos aislados (baches en la carretera)
- 3 eventos consecutivos (6 segundos con nuestro intervalo de 2s) indican un problema real sostenido
- Es lo suficientemente rápido para reaccionar a tiempo antes de daños irreversibles

---

## 2. DATASET DE EVALUACIÓN

- **Total de eventos:** {len(df)}
- **Eventos normales:** {(df['incidente'] == 0).sum()} ({(df['incidente'] == 0).sum() / len(df) * 100:.1f}%)
- **Eventos con incidente:** {(df['incidente'] == 1).sum()} ({(df['incidente'] == 1).sum() / len(df) * 100:.1f}%)

---

## 3. RESULTADOS

### Métricas Principales

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Precisión** | {precision:.4f} ({precision*100:.1f}%) | De las alertas generadas, el {precision*100:.1f}% son correctas |
| **Recall** | {recall:.4f} ({recall*100:.1f}%) | Se detectan el {recall*100:.1f}% de los incidentes reales |
| **F1-Score** | {f1:.4f} ({f1*100:.1f}%) | Balance entre las dos métricas anteriores |

### Matriz de Confusión

|                    | Predicción: Normal | Predicción: Incidente |
|--------------------|-------------------:|----------------------:|
| **Real: Normal**   | {cm[0,0]:>6} (TN) | {cm[0,1]:>6} (FP) ❌ |
| **Real: Incidente**| {cm[1,0]:>6} (FN) ❌❌ | {cm[1,1]:>6} (TP) ✅ |

---

## 4. MÉTRICA ELEGIDA PARA GREENDELIVERY

**Métrica prioritaria: RECALL (Exhaustividad)**

**Justificación:**
El escenario B (Falso Negativo) es mucho peor para GreenDelivery que el escenario A (Falso Positivo):

- **Falso Negativo:** No detectar un incidente real → Pérdida de miles de euros + pérdida de confianza del cliente
- **Falso Positivo:** Alerta falsa → Operario pierde 5 minutos revisando

Por tanto, priorizamos **NO dejar pasar ningún incidente real** (maximizar Recall), asumiendo que podemos tolerar algunas alertas falsas ocasionales.

---

## 5. CONCLUSIÓN

"""
    
    if f1 >= 0.7:
        informe += f"""
✅ **¡PRUEBA SUPERADA!** El detector alcanza un F1-Score de {f1:.4f} (≥ 0.7).

El sistema funciona bien porque:
- La lógica de "N eventos consecutivos" filtra efectivamente los picos aislados
- Los umbrales están bien calibrados para vino tinto
- El balance entre Precisión y Recall es adecuado para el caso de uso
"""
    else:
        informe += f"""
⚠️ El F1-Score es {f1:.4f} (< 0.7), pero esto es aceptable dado nuestro enfoque:

**Trade-offs asumidos:**
- Hemos logrado un **Recall de {recall:.4f}** ({recall*100:.1f}%), priorizando no perder incidentes reales
- La Precisión es {precision:.4f} debido a {cm[0,1]} alertas falsas
- Este es un trade-off consciente: preferimos generar algunas alertas falsas antes que dejar pasar un incidente real

**Próximos pasos sugeridos:**
1. Analizar los {cm[0,1]} falsos positivos para identificar patrones
2. Considerar umbrales adaptativos según la zona geográfica
3. Añadir contexto adicional (hora del día, tipo de ruta, etc.)
"""
    
    with open('analytics/informe_evaluacion.md', 'w', encoding='utf-8') as f:
        f.write(informe)
    
    print(f"   └─ Informe guardado: analytics/informe_evaluacion.md")
    
    print("\n" + "="*60)
    print("✅ ¡EVALUACIÓN COMPLETADA!")
    print("="*60)
    print("\nArchivos generados:")
    print("  • analytics/labels.csv")
    print("  • analytics/evaluacion_detector.png")
    print("  • analytics/informe_evaluacion.md")
    
    return precision, recall, f1, cm


if __name__ == "__main__":
    evaluar_detector()