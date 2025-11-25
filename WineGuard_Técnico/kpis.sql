-- ============================================
-- CONSULTAS SQL PARA LOS 3 KPIs PRINCIPALES
-- ============================================

-- ============================================
-- KPI 1: % DE ENVÍOS EN SLA (Tasa de Éxito)
-- ============================================
-- Pregunta: ¿Qué % de paquetes llegan sin problemas?
-- Meta: > 95%

WITH paquetes_con_alertas AS (
    SELECT DISTINCT id_paquete
    FROM alerts
),
todos_los_paquetes AS (
    SELECT DISTINCT id_paquete
    FROM telemetry
)
SELECT 
    COUNT(DISTINCT t.id_paquete) as total_paquetes,
    COUNT(DISTINCT t.id_paquete) - COUNT(DISTINCT a.id_paquete) as paquetes_sin_alertas,
    ROUND(
        ((COUNT(DISTINCT t.id_paquete)::float - COUNT(DISTINCT a.id_paquete)::float) / 
         COUNT(DISTINCT t.id_paquete)::float) * 100, 
        2
    ) as porcentaje_sla
FROM todos_los_paquetes t
LEFT JOIN paquetes_con_alertas a ON t.id_paquete = a.id_paquete;


-- ============================================
-- KPI 2: TIEMPO MEDIO DE DETECCIÓN (MTTD)
-- ============================================
-- Pregunta: ¿Cuánto tardamos en detectar un problema?
-- Meta: < 30 segundos

WITH tiempos_deteccion AS (
    SELECT 
        a.id,
        a.id_paquete,
        a.tipo_incidente,
        a.timestamp_inicio,
        -- Buscar el primer evento anómalo en telemetría
        MIN(t.timestamp) as primer_evento_anomalo,
        -- Calcular diferencia en segundos
        EXTRACT(EPOCH FROM (
            a.created_at::timestamp - 
            MIN(t.timestamp)::timestamp
        )) as segundos_hasta_alerta
    FROM alerts a
    INNER JOIN telemetry t ON a.id_paquete = t.id_paquete
    WHERE 
        -- Para temperatura: eventos con temp > 8°C
        (a.tipo_incidente = 'temperatura_alta' AND t.temperatura > 8.0)
        OR
        -- Para choque: eventos con fuerza_g > 2.5 e inclinación > 30
        (a.tipo_incidente = 'choque' AND t.fuerza_g > 2.5 AND t.inclinacion > 30)
    GROUP BY a.id, a.id_paquete, a.tipo_incidente, a.timestamp_inicio, a.created_at
)
SELECT 
    COUNT(*) as total_alertas,
    ROUND(AVG(segundos_hasta_alerta)::numeric, 2) as mttd_segundos,
    ROUND(MIN(segundos_hasta_alerta)::numeric, 2) as deteccion_mas_rapida,
    ROUND(MAX(segundos_hasta_alerta)::numeric, 2) as deteccion_mas_lenta,
    CASE 
        WHEN AVG(segundos_hasta_alerta) < 30 THEN '✅ Excelente (< 30s)'
        WHEN AVG(segundos_hasta_alerta) < 60 THEN '⚠️ Aceptable (30-60s)'
        ELSE '❌ Necesita mejora (> 60s)'
    END as valoracion
FROM tiempos_deteccion;


-- ============================================
-- KPI 3: % DE FALSOS POSITIVOS
-- ============================================
-- Pregunta: ¿Cuántas alertas son falsas alarmas?
-- Meta: < 10%

-- NOTA: Para este KPI necesitamos una tabla de "validaciones"
-- donde los operarios marquen si una alerta fue correcta o no.

-- Primero, crear la tabla si no existe:
CREATE TABLE IF NOT EXISTS alert_validations (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    es_falso_positivo BOOLEAN NOT NULL,
    validado_por VARCHAR(50),
    comentario TEXT,
    validado_en TIMESTAMP DEFAULT NOW()
);

-- Consulta del KPI (solo funcionará si hay validaciones):
SELECT 
    COUNT(*) as total_alertas_validadas,
    SUM(CASE WHEN es_falso_positivo THEN 1 ELSE 0 END) as falsos_positivos,
    ROUND(
        (SUM(CASE WHEN es_falso_positivo THEN 1 ELSE 0 END)::float / 
         COUNT(*)::float) * 100,
        2
    ) as porcentaje_falsos_positivos,
    CASE 
        WHEN (SUM(CASE WHEN es_falso_positivo THEN 1 ELSE 0 END)::float / COUNT(*)::float) * 100 < 10 THEN '✅ Excelente'
        WHEN (SUM(CASE WHEN es_falso_positivo THEN 1 ELSE 0 END)::float / COUNT(*)::float) * 100 < 20 THEN '⚠️ Aceptable'
        ELSE '❌ Crítico - Fatiga de alertas'
    END as valoracion
FROM alert_validations;

-- NOTA: Como aún no tenemos validaciones reales, podemos simularlas:
-- (Para la demo, asumimos que el 15% son falsos positivos)
SELECT 
    COUNT(*) as total_alertas,
    ROUND(COUNT(*) * 0.15) as falsos_positivos_estimados,
    15.0 as porcentaje_falsos_positivos_estimado,
    '⚠️ Aceptable (estimado)' as valoracion
FROM alerts;


-- ============================================
-- VISTA CONSOLIDADA: DASHBOARD PRINCIPAL
-- ============================================
CREATE OR REPLACE VIEW dashboard_kpis AS
WITH 
-- KPI 1: SLA
sla AS (
    SELECT 
        ROUND(
            ((COUNT(DISTINCT t.id_paquete)::float - COUNT(DISTINCT a.id_paquete)::float) / 
             COUNT(DISTINCT t.id_paquete)::float) * 100, 
            2
        ) as porcentaje_sla
    FROM (SELECT DISTINCT id_paquete FROM telemetry) t
    LEFT JOIN (SELECT DISTINCT id_paquete FROM alerts) a ON t.id_paquete = a.id_paquete
),
-- KPI 2: MTTD (simplificado - cuenta eventos hasta la alerta)
mttd AS (
    SELECT 
        ROUND(AVG(num_eventos * 2.0)::numeric, 2) as mttd_segundos  -- 2s por evento
    FROM alerts
),
-- KPI 3: Falsos Positivos (estimado)
falsos_positivos AS (
    SELECT 
        COUNT(*) as total_alertas,
        ROUND(COUNT(*) * 0.15) as falsos_positivos,
        15.0 as porcentaje_fp
    FROM alerts
)
SELECT 
    (SELECT porcentaje_sla FROM sla) as kpi_sla_porcentaje,
    (SELECT mttd_segundos FROM mttd) as kpi_mttd_segundos,
    (SELECT porcentaje_fp FROM falsos_positivos) as kpi_falsos_positivos_porcentaje;


-- Consultar la vista:
SELECT * FROM dashboard_kpis;


-- ============================================
-- CONSULTAS ADICIONALES ÚTILES
-- ============================================

-- Ver histórico de alertas por paquete
SELECT 
    id_paquete,
    COUNT(*) as num_alertas,
    STRING_AGG(DISTINCT tipo_incidente, ', ') as tipos_incidentes
FROM alerts
GROUP BY id_paquete
ORDER BY num_alertas DESC;

-- Evolución de alertas en el tiempo
SELECT 
    DATE(created_at) as fecha,
    COUNT(*) as alertas_del_dia,
    STRING_AGG(DISTINCT tipo_incidente, ', ') as tipos
FROM alerts
GROUP BY DATE(created_at)
ORDER BY fecha DESC;

-- Análisis de incidentes por tipo
SELECT 
    tipo_incidente,
    COUNT(*) as cantidad,
    ROUND(AVG(num_eventos)::numeric, 2) as eventos_promedio,
    ROUND(AVG(valor_max)::numeric, 2) as valor_max_promedio,
    ROUND(AVG(valor_promedio)::numeric, 2) as valor_promedio_promedio
FROM alerts
GROUP BY tipo_incidente;