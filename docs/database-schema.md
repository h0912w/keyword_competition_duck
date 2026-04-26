# SQLite 스키마

```sql
CREATE TABLE IF NOT EXISTS keyword_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_index INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    keyword_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    top10_title_match_count INTEGER DEFAULT -1,
    error_message TEXT DEFAULT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword_hash)
);
CREATE INDEX IF NOT EXISTS idx_status ON keyword_measurements(status);
CREATE INDEX IF NOT EXISTS idx_original_idx ON keyword_measurements(original_index);
CREATE INDEX IF NOT EXISTS idx_keyword_hash ON keyword_measurements(keyword_hash);
```

상태 값: `PENDING`, `RUNNING`, `DONE`, `FAILED`, `SKIPPED_DUPLICATE`.
