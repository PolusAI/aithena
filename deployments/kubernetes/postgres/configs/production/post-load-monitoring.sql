-- =================================================================
-- Post-Load Monitoring Setup Script
-- Run this after switching to production configuration
-- =================================================================

-- Ensure pg_stat_statements extension is loaded
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Reset pg_stat_statements to start fresh
SELECT pg_stat_statements_reset();

-- Enable tracking
ALTER SYSTEM SET pg_stat_statements.track = 'all';
SELECT pg_reload_conf();

-- Note: No additional indexes are created here
-- All necessary indexes should be created by the add_constraints.py script

-- Analyze all tables to update statistics
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT schemaname, tablename 
        FROM pg_tables 
        WHERE schemaname = 'openalex'
    LOOP
        RAISE NOTICE 'Analyzing %.%', r.schemaname, r.tablename;
        EXECUTE format('ANALYZE %I.%I', r.schemaname, r.tablename);
    END LOOP;
END $$;

-- Verify monitoring is working
SELECT 
    'pg_stat_statements enabled' AS check,
    CASE 
        WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements') 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END AS status
UNION ALL
SELECT 
    'Monitoring schema exists',
    CASE 
        WHEN EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'monitoring') 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END
UNION ALL
SELECT 
    'Monitoring views created',
    CASE 
        WHEN EXISTS (SELECT 1 FROM pg_views WHERE schemaname = 'monitoring' AND viewname = 'slow_queries') 
        THEN 'PASS' 
        ELSE 'FAIL' 
    END;

-- Show current configuration
SHOW shared_preload_libraries;
SHOW pg_stat_statements.track;

-- Quick stats
SELECT 
    'Tables in openalex schema' AS metric,
    COUNT(*)::text AS value
FROM pg_tables 
WHERE schemaname = 'openalex'
UNION ALL
SELECT 
    'Total database size',
    pg_size_pretty(pg_database_size(current_database()))
UNION ALL
SELECT 
    'Largest table',
    tablename || ' (' || pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) || ')'
FROM pg_tables
WHERE schemaname = 'openalex'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 1;

\echo ''
\echo 'Monitoring setup complete!'
\echo 'You can now use:'
\echo '  - SELECT * FROM monitoring.slow_queries;'
\echo '  - SELECT * FROM monitoring.table_sizes;'
\echo '  - SELECT * FROM monitoring.index_usage;'
\echo '  - SELECT * FROM monitoring.current_activity;'
\echo '  - SELECT * FROM monitoring.table_bloat;'
