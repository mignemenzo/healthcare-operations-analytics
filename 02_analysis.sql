-- =============================================
-- 1. DATA CLEANING & STANDARDIZATION
-- =============================================

-- Remove duplicates from specimens table
DELETE FROM specimens
WHERE specimen_id IN (
    SELECT specimen_id
    FROM (
        SELECT specimen_id, ROW_NUMBER() OVER (PARTITION BY specimen_id ORDER BY collection_time DESC) as row_num
        FROM specimens
    ) t
    WHERE row_num > 1
);

-- Fix negative Turnaround Times (TAT)
-- Assuming resulted_time cannot be before received_time
UPDATE specimens
SET resulted_time = received_time
WHERE resulted_time < received_time;

-- Standardize Department Names (Example: 'Hem' -> 'Hematology')
UPDATE analyzers
SET department = 'Hematology'
WHERE department IN ('Hem', 'Heme');

-- =============================================
-- 2. FEATURE ENGINEERING
-- =============================================

-- Add calculated columns for TAT and Time in Lab
ALTER TABLE specimens ADD COLUMN turnaround_time_minutes INTEGER;
ALTER TABLE specimens ADD COLUMN time_in_lab_minutes INTEGER;

UPDATE specimens
SET turnaround_time_minutes = (strftime('%s', resulted_time) - strftime('%s', received_time)) / 60,
    time_in_lab_minutes = (strftime('%s', resulted_time) - strftime('%s', collection_time)) / 60;

-- =============================================
-- 3. ANALYTICAL QUERIES
-- =============================================

-- Query 1: Average Turnaround Time (TAT) by Test Type and Priority
SELECT 
    test_type,
    priority,
    ROUND(AVG(turnaround_time_minutes), 2) as avg_tat_minutes,
    COUNT(*) as total_volume
FROM specimens
GROUP BY test_type, priority
ORDER BY test_type, priority;

-- Query 2: QC Failure Rate by Analyzer
SELECT 
    a.analyzer_name,
    q.analyzer_id,
    COUNT(*) as total_qc_runs,
    SUM(CASE WHEN q.result = 'Fail' THEN 1 ELSE 0 END) as failed_qc_runs,
    ROUND(CAST(SUM(CASE WHEN q.result = 'Fail' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) as failure_rate_pct
FROM qc_events q
JOIN analyzers a ON q.analyzer_id = a.analyzer_id
GROUP BY a.analyzer_name, q.analyzer_id
ORDER BY failure_rate_pct DESC;

-- Query 3: High-Risk Bottleneck Hours (Avg TAT > 60 mins for STAT)
SELECT 
    strftime('%H', received_time) as hour_of_day,
    ROUND(AVG(turnaround_time_minutes), 2) as avg_stat_tat
FROM specimens
WHERE priority = 'STAT'
GROUP BY hour_of_day
HAVING avg_stat_tat > 45
ORDER BY avg_stat_tat DESC;

-- Query 4: Downtime Impact Analysis
-- Correlate daily downtime with daily average TAT
SELECT 
    s.date,
    a.analyzer_name,
    a.downtime_minutes,
    ROUND(AVG(sp.turnaround_time_minutes), 2) as daily_avg_tat
FROM analyzers a
JOIN (
    SELECT 
        date(received_time) as date, 
        analyzer_id, 
        turnaround_time_minutes 
    FROM specimens
) sp ON a.analyzer_id = sp.analyzer_id AND a.date = sp.date
JOIN (
    SELECT DISTINCT date FROM analyzers
) s ON a.date = s.date
GROUP BY s.date, a.analyzer_name, a.downtime_minutes
ORDER BY a.downtime_minutes DESC
LIMIT 20;
