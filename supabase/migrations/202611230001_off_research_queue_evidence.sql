-- Add traceability fields to the review-only Open Food Facts queue.
-- Existing rows are preserved; new fields are nullable except the safe false default.
alter table public.jhc_ingredient_research_queue
  add column if not exists collected_at timestamptz,
  add column if not exists verification_status text,
  add column if not exists source_license text,
  add column if not exists source_attribution text,
  add column if not exists halal_certified boolean not null default false;

comment on column public.jhc_ingredient_research_queue.collected_at is
  'Source capture time; created_at remains the database import time.';
comment on column public.jhc_ingredient_research_queue.verification_status is
  'Evidence state; Open Food Facts rows remain community-contributed and human-review pending.';
comment on column public.jhc_ingredient_research_queue.source_license is
  'Data reuse licence for the source database/content.';
comment on column public.jhc_ingredient_research_queue.source_attribution is
  'Attribution text required by the source licence.';
comment on column public.jhc_ingredient_research_queue.halal_certified is
  'False by default; this queue never grants halal certification.';
