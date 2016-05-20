-- Inspired by EB's answer at http://stackoverflow.com/questions/244243/how-to-reset-postgres-primary-key-sequence-when-it-falls-out-of-sync

-- Function to reset a sequence to the MAX of its associated column (or 1 if the column is empty)
CREATE OR REPLACE FUNCTION "reset_sequence" (tablename text, columnname text)
RETURNS INTEGER AS
$body$
DECLARE
  new_next_val INTEGER;
BEGIN
  EXECUTE 'SELECT setval( pg_get_serial_sequence(''' || tablename || ''', ''' || columnname || '''),
           (SELECT COALESCE(MAX(' || columnname || ') + 1, 1) FROM ' || tablename || '), false)' INTO new_next_val;
  RETURN new_next_val;
END;
$body$  LANGUAGE 'plpgsql';

-- Reset all sequences in 'migrated' schema. Note that if you want to change the schema this applies to,
-- it's currently hard-coded in three places!
SELECT 'migrated."' || table_name || '".' || column_name AS col_seq_updated,
       reset_sequence('migrated."' || table_name || '"', column_name) AS new_next_value
FROM information_schema.columns
WHERE table_schema = 'migrated'
  AND column_default LIKE 'nextval%';
