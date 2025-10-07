# Materialized View for Works Authorships Performance Optimization

## Overview
This document describes a materialized view optimization for improving the performance of similarity searches that join works_authorships with authors to get display names.

## Current Performance Issue
The current query performs a JOIN between `openalex.works_authorships` and `openalex.authors` for every similarity search, which can be slow with large datasets.

## Proposed Solution: Materialized View

### 1. Create the Materialized View
```sql
-- Create materialized view that pre-joins authorships with author names
CREATE MATERIALIZED VIEW openalex.works_authorships_with_names AS
SELECT 
    wa.work_id,
    wa.author_position,
    wa.author_id,
    wa.institution_id,
    wa.raw_affiliation_string,
    a.display_name
FROM openalex.works_authorships wa
JOIN openalex.authors a ON wa.author_id = a.id;

-- Create index for fast lookups
CREATE INDEX ON openalex.works_authorships_with_names (work_id);

-- Optional: Create additional indexes if needed
CREATE INDEX ON openalex.works_authorships_with_names (author_id);
```

### 2. Create it CONCURRENTLY (to avoid blocking)
```sql
-- For production use, create without blocking other operations
CREATE MATERIALIZED VIEW CONCURRENTLY openalex.works_authorships_with_names AS
SELECT 
    wa.work_id,
    wa.author_position,
    wa.author_id,
    wa.institution_id,
    wa.raw_affiliation_string,
    a.display_name
FROM openalex.works_authorships wa
JOIN openalex.authors a ON wa.author_id = a.id;

-- Also create index concurrently
CREATE INDEX CONCURRENTLY ON openalex.works_authorships_with_names (work_id);
```

### 3. Update the Query
Once the materialized view is created, update the similarity search query to use it:

```python
# In works_by_similarity_search function, replace the table reference:
# FROM openalex.works_authorships wa
# JOIN openalex.authors a ON wa.author_id = a.id

# With:
# FROM openalex.works_authorships_with_names wa
```

### 4. Refresh Strategy
The materialized view needs to be refreshed when the underlying data changes:

```sql
-- Manual refresh (blocks queries)
REFRESH MATERIALIZED VIEW openalex.works_authorships_with_names;

-- Concurrent refresh (doesn't block queries, but requires a unique index)
CREATE UNIQUE INDEX ON openalex.works_authorships_with_names (work_id, author_position);
REFRESH MATERIALIZED VIEW CONCURRENTLY openalex.works_authorships_with_names;
```

### 5. Automated Refresh Options

#### Option A: Cron Job
```bash
# Add to crontab - refresh daily at 2 AM
0 2 * * * psql -U postgres -d askaithena -c "REFRESH MATERIALIZED VIEW CONCURRENTLY openalex.works_authorships_with_names;"
```

#### Option B: PostgreSQL Extension (pg_cron)
```sql
-- Install pg_cron extension
CREATE EXTENSION pg_cron;

-- Schedule daily refresh
SELECT cron.schedule('refresh-authorships-view', '0 2 * * *', 
    'REFRESH MATERIALIZED VIEW CONCURRENTLY openalex.works_authorships_with_names;');
```

#### Option C: Trigger-based (for real-time updates)
```sql
-- Create a function to refresh the view
CREATE OR REPLACE FUNCTION refresh_authorships_view()
RETURNS TRIGGER AS $$
BEGIN
    -- Use CONCURRENTLY in production
    REFRESH MATERIALIZED VIEW CONCURRENTLY openalex.works_authorships_with_names;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create triggers on source tables
CREATE TRIGGER refresh_authorships_view_on_authors
AFTER INSERT OR UPDATE OR DELETE ON openalex.authors
FOR EACH STATEMENT EXECUTE FUNCTION refresh_authorships_view();

CREATE TRIGGER refresh_authorships_view_on_works_authorships
AFTER INSERT OR UPDATE OR DELETE ON openalex.works_authorships
FOR EACH STATEMENT EXECUTE FUNCTION refresh_authorships_view();
```

## Performance Expectations

### Time Estimates
- **Initial Creation**: ~5-15 minutes (for ~500M authorships)
- **Index Creation**: ~2-5 minutes
- **Total**: ~7-20 minutes

### Space Requirements
- Approximately 50-100GB additional disk space
- Depends on the number of authorships and size of display names

### Performance Improvement
- Eliminates JOIN operation during queries
- Expected 2-5x performance improvement for similarity searches
- Reduces CPU usage during peak query times

## Monitoring

### Check Materialized View Size
```sql
SELECT 
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||matviewname)) as size
FROM pg_matviews
WHERE matviewname = 'works_authorships_with_names';
```

### Check Last Refresh Time
```sql
SELECT 
    schemaname,
    matviewname,
    last_refresh
FROM pg_matviews_stats
WHERE matviewname = 'works_authorships_with_names';
```

### Monitor Refresh Performance
```sql
-- During refresh, monitor progress
SELECT * FROM pg_stat_progress_create_index;
```

## Rollback Plan
If the materialized view causes issues:

```sql
-- Drop the materialized view
DROP MATERIALIZED VIEW IF EXISTS openalex.works_authorships_with_names;

-- Revert code to use original tables
-- (Keep the original query as a fallback)
```

## Implementation Checklist
- [ ] Test on a subset of data first
- [ ] Measure current query performance baseline
- [ ] Create materialized view during low-traffic period
- [ ] Update application code to use new view
- [ ] Set up refresh schedule
- [ ] Monitor performance improvements
- [ ] Document the change in deployment notes

## Notes
- The materialized view trades disk space for query performance
- Consider the data freshness requirements when choosing refresh frequency
- CONCURRENT operations require PostgreSQL 9.4+
- For very large datasets, consider partitioning the materialized view
