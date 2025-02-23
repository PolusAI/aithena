identify index building queries

```sql
SELECT
    pid,
    usename,
    datname,
    state,
    query,
    query_start
FROM
    pg_stat_activity
WHERE
    query LIKE '%CREATE INDEX%'
    AND state = 'active';
```

Or try to figure out index progress

```sql
SELECT
    pid,
    datname,
    relid::regclass AS table_name,
    index_relid::regclass AS index_name,
    phase,
    round(100.0 * blocks_done / nullif(blocks_total, 0), 1) AS progress_percent,
    blocks_done,
    blocks_total,
    tuples_done,
    tuples_total
FROM
    pg_stat_progress_create_index;
```



terminate a backend query:

SELECT pg_terminate_backend(<pid>);

-------------

SELECT phase, round(100.0 * blocks_done / nullif(blocks_total, 0), 1) AS "%" FROM pg_stat_progress_create_index;