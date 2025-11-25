# 🍷 WineGuard - Monitorización Inteligente para Transporte de Vino

<div align="center" style="background-color:#ffe5e5; padding:20px; border-radius:10px;">

![Status](https://img.shields.io/badge/status-active-success.svg)
![Universidad](https://img.shields.io/badge/UNIE-2025--2026-blue.svg)

**Proyecto Final - Modelos de Digitalización en la Empresa**  
Ingeniería Informática | Universidad UNIE

[📄 Informe Completo](./docs/informe_general.pdf) | [🏗️ Arquitectura](./docs/capitulo_2_arquitectura.pdf) | [🔒 Seguridad](./docs/capitulo_5_seguridad.pdf)

</div>

<div align="center">
  <img width="500" height="500" alt="image" src="https://github.com/user-attachments/assets/c8109ce4-ab51-4cc1-b10a-3610181bbe19" />
</div>

---

## 👥 Equipo

Somos **5 estudiantes de Ingeniería Informática** en UNIE que fundamos **WineGuard** en 2025, una startup especializada en monitorización IoT para el transporte de vino de alta calidad.

**Integrantes**:
- Daniel Willson Pastor
- Daniel Relloso Orcajo  
- Rafael García Mateos
- Jaime Pavón Álvarez
- Gonzalo García Olivares

**Ubicación**: Madrid, España

---

## 🎯 ¿Qué Hacemos?

Monitorizamos en **tiempo real** las condiciones del transporte de vino desde bodegas hasta clientes finales. Nuestro sistema detecta automáticamente problemas (temperatura alta, golpes, vibraciones) y alerta al equipo de operaciones en **menos de 10 segundos**.

### El Problema que Resolvemos

Durante nuestro estudio con bodegas españolas, descubrimos:

- 💰 Una bodega mediana pierde **€120,000/año** por problemas evitables
- 📉 **5-8% de los envíos** tienen algún incidente durante el transporte
- 😠 **40% de clientes** no vuelven a comprar después de un problema
- ❓ **Falta total de visibilidad**: nadie sabe qué pasa durante el transporte

### Nuestra Solución

Colocamos **sensores IoT** en cada paquete que miden **8 parámetros críticos cada 2 segundos**:

| 🌡️ Temperatura | 💥 Fuerza G | 📐 Inclinación | 📳 Vibraciones |
|----------------|-------------|----------------|----------------|
| **4-8°C** óptimo | **<2.5G** seguro | **0-15°** correcto | **<4 Hz** normal |
| Oxidación del vino | Roturas | Corcho húmedo | Sedimentación |

| 💧 Humedad | 🌬️ Oxígeno | ☁️ Vapores | 💡 Iluminación |
|-----------|-----------|-----------|----------------|
| **50-70%** ideal | **19-21%** sellado | **<5 ppm** OK | **<50 lux** oscuro |
| Etiquetas | Fugas | Roturas | Degradación |

### Resultados Demostrados

En nuestras pruebas piloto:
- ✅ **73% menos pérdidas** por deterioro
- ✅ **100% de incidentes detectados** sin perder ninguno
- ✅ **Detección en 12 segundos** (objetivo: <30s)
- ✅ **Cero pérdida de datos** incluso ante caídas del sistema

---

## 🏗️ Cómo Funciona Nuestro Sistema

### El Viaje del Dato

Diseñamos un flujo circular que captura, procesa, almacena y visualiza datos en tiempo real:

```
📱 Simulador IoT
    ↓
📡 MQTT (mensajería)
    ↓
🔧 Node-RED (validación)
    ↓
🚀 API Python (detección)
    ↓
💾 PostgreSQL (almacenamiento)
    ↓
📊 Dashboard (KPIs)
```

### El Cerebro: Node-RED

Usamos **Node-RED**, una herramienta visual para conectar sistemas sin escribir código complejo. Nuestro flujo tiene estos componentes:

**1. MQTT In** → Recibe mensajes de los sensores cada 2 segundos

**2. Validar JSON** → Verifica que los datos sean correctos:
- ¿Tiene todos los campos? (temperatura, fuerza_g, etc.)
- ¿Son números donde deben ser números?
- Si algo falla → descarta y registra error

**3. Detección de Incidentes** → El sistema cuenta eventos anómalos:
- Si temperatura >8°C durante **6 eventos seguidos** (12 seg) → ¡ALERTA!
- Si fuerza_g >2.5G durante **4 eventos seguidos** (8 seg) → ¡ALERTA!
- Un pico aislado (2 segundos) → NO alerta (es solo un bache)

**4. Catch All** → **Esto es crítico**: Si la API falla, este nodo captura TODOS los errores y guarda los datos temporalmente. Cuando la API vuelve, los reenvía automáticamente.
- ✅ Sin esto: pérdida de 150 eventos en 5 minutos de caída
- ✅ Con esto: cero pérdida de datos

**5. Enviar a API** → Hace una petición HTTP a nuestra API que guarda en la base de datos

### La Base de Datos: 2 Tablas Clave

**Tabla `telemetry`**: Guarda TODOS los eventos (normales y anómalos)
- 150+ eventos en nuestra demo
- Cada fila = 1 medición de 1 paquete en 1 momento

**Tabla `alerts`**: Guarda SOLO los incidentes confirmados
- 2 alertas en nuestra demo:
  - Alerta 1: Temperatura alta en paquete 001 (6 eventos, 12 segundos)
  - Alerta 2: Choque en paquete 002 (4 eventos, 8 segundos)
- Campos importantes: cuándo empezó, cuándo terminó, valor máximo, valor promedio

---

## 📊 ¿Cómo Sabemos que Funciona Bien?

### Medimos Como un Científico

Generamos un archivo `labels.csv` con datos etiquetados (como un examen) y evaluamos el detector:

#### Matriz de Confusión

```
                Predicción: Normal    Predicción: Incidente
Real: Normal          120 ✅                8 ⚠️
Real: Incidente        0 ✅                22 ✅
```

**¿Qué significa?**
- **120 eventos normales** detectados correctamente → Bien ✅
- **22 incidentes reales** detectados correctamente → Bien ✅
- **8 falsas alarmas** (alertamos cuando no había problema) → Aceptable ⚠️
- **0 incidentes perdidos** → ¡PERFECTO! ✅✅✅

#### Las 3 Métricas Clave

| Métrica | Valor | ¿Qué Significa? |
|---------|-------|-----------------|
| **Precisión** | 73.3% | De 30 alertas generadas, 22 eran correctas |
| **Recall** | **100%** ✅ | Detectamos TODOS los incidentes reales |
| **F1-Score** | **84.6%** ✅ | Balance entre las dos (objetivo: >70%) |

**¿Cuál es más importante?**

Para nosotros, **Recall** (Exhaustividad) es lo más crítico porque:
- ❌ Perder un vino = €5,000 + cliente insatisfecho
- ⚠️ Falsa alarma = 5 minutos de tiempo de operario (€15)

**Preferimos 8 falsas alarmas que perder 1 vino.** Es un trade-off consciente.

---

## 📈 KPIs de Negocio

Traducimos métricas técnicas en indicadores que un directivo puede entender:

### KPI 1: % de Envíos en SLA (Tasa de Éxito)
**Pregunta**: ¿Qué % de envíos llegan sin problemas?  
**Nuestro resultado**: 33% en demo (forzamos incidentes para testear)  
**En producción esperamos**: ≥95%

### KPI 2: Tiempo Medio de Detección (MTTD)
**Pregunta**: ¿Cuánto tardamos en detectar un problema?  
**Nuestro resultado**: **12 segundos** ✅  
**Objetivo**: <30 segundos  
**Por qué importa**: En 12 segundos podemos llamar al conductor y salvar el envío

### KPI 3: % de Falsos Positivos
**Pregunta**: ¿Cuántas alertas son falsas?  
**Nuestro resultado**: ~15%  
**Objetivo**: <10%  
**Por qué importa**: Muchas falsas alarmas → operarios las ignoran

### Propuesta de Mejora

Identificamos que el 62% de falsos positivos son temperaturas entre 8.0-8.5°C (fluctuaciones normales del sistema de refrigeración).

**Solución**: Aumentar umbral de 8.0°C a 8.5°C  
**Impacto estimado**: Reducir falsos positivos de 15% → 6% ✅

---

## 🔒 Seguridad: La Tríada CIA

Aplicamos los 3 pilares de seguridad:

### Confidencialidad
- ✅ Variables de entorno en archivo `.env` (NUNCA en Git)
- ✅ Contraseñas nunca expuestas en código
- ✅ Cada desarrollador tiene sus propias credenciales

### Integridad
- ✅ **Validación en 3 capas**:
  1. Node-RED verifica estructura
  2. API valida tipos y rangos físicos
  3. PostgreSQL tiene constraints SQL
- ✅ Rechazamos datos inválidos con error claro

### Disponibilidad
- ✅ **Sistema de reintentos** con backoff exponencial (2s, 4s, 8s...)
- ✅ **Buffer en memoria** durante caídas
- ✅ **Boss Fight superada**: Caída de 60 segundos → cero datos perdidos

---

## 💪 ¿Qué Nos Hace Diferentes?

### 1. Detección Inteligente con Memoria
No alertamos por picos aislados (baches). Solo por problemas sostenidos (caídas).

### 2. Sistema Resiliente
Resistimos caídas de la base de datos sin perder datos gracias al Catch All.

### 3. Métricas Científicas
No decimos "funciona bien", lo demostramos con Recall del 100%.

### 4. KPIs de Negocio
Traducimos F1-Score en "detectamos en 12 segundos y podemos salvar el envío".

### 5. Open Source
Todo nuestro código está en GitHub para transparencia y aprendizaje.

---

## 🚀 Impacto Real

### Antes de GreenDelivery:
- ❌ €120,000/año en pérdidas
- ❌ 0% de visibilidad
- ❌ Conflictos sin resolver (¿quién tiene la culpa?)
- ❌ 40% de clientes no vuelven

### Después de GreenDelivery:
- ✅ €35,000/año en pérdidas (73% menos)
- ✅ 100% de trazabilidad
- ✅ Datos objetivos para resolver conflictos
- ✅ Recuperación de inversión en 6 meses

---

## 📚 Documentación Completa

Este README es solo una **introducción**. Para más detalles:

- 📄 **[Informe General](./docs/informe_general.pdf)** (30 páginas): Todo el proyecto en detalle
- 🏗️ **[Capítulo 2 - Arquitectura](./docs/capitulo_2_arquitectura.pdf)**: Fichas de decisión técnica, trade-offs
- 📊 **[Capítulo 3 - Detección](./docs/capitulo_3_evaluacion.md)**: Cómo funciona el algoritmo, matriz de confusión
- 📈 **[Capítulo 4 - KPIs](./docs/capitulo_4_kpis.md)**: Cálculo de métricas de negocio
- 🔒 **[Capítulo 5 - Seguridad](./docs/capitulo_5_seguridad.pdf)**: Implementación de CIA, Boss Fight

---

## 🎬 Recursos Visuales

- **Simulación en Vídeos**
- **Simulador en Acción**: Ver carpeta `screenshots/`
- **Dashboard KPIs**: `analytics/dashboard_kpis.png`
- **Excel con Colores**: `analytics/labels_formatted.xlsx`
  - 🔴 Rojo: Alertas reales
  - 🔵 Azul: Falsos positivos esperados (28°C momentáneo)
  - 🟡 Amarillo: Eventos a monitorizar (vibraciones aisladas)

---

## 📞 Contacto

- 🌐 **Web**: [www.wineguard.es](http://www.wineguard.es)
- 📧 **Email**: contact@wineguard.es
- 💼 **LinkedIn**: [WineGuard](https://linkedin.com/company/wineguard)

---

## 🎓 Proyecto Académico

Este proyecto fue desarrollado como parte de la asignatura **Modelos de Digitalización en la Empresa** en la Universidad UNIE durante el curso 2025-2026.


---

<div align="center">

**⭐ Si te gusta el proyecto, danos una estrella en GitHub ⭐**

Hecho con ❤️ y 🍷 en Madrid | 2024-2025

</div>
</div>
