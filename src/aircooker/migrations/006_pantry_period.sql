ALTER TABLE pantry_item ADD COLUMN include_week_start TEXT
 CHECK(include_week_start IS NULL OR
 (length(include_week_start)=10 AND date(include_week_start)=include_week_start
 AND strftime('%w',include_week_start)='1'));
