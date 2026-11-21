-- Preserve valid Japanese JAN-8 and JAN-13 values in the ingredient research staging table.
-- Existing identity keys and ingredient records are unchanged.
ALTER TABLE public.jhc_crawler_ingredient_staging
  DROP CONSTRAINT IF EXISTS jan_only_explicit;

ALTER TABLE public.jhc_crawler_ingredient_staging
  ADD CONSTRAINT jan_only_explicit
  CHECK (jan_code IS NULL OR jan_code ~ '^(?:[0-9]{8}|[0-9]{13})$');
