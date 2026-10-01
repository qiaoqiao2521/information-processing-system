-- Private editorial drafts. No publication exists before explicit human approval.
CREATE TABLE upstream_reviews (
  id text PRIMARY KEY,
  source_hash text NOT NULL,
  source jsonb NOT NULL,
  draft jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','rejected','stale','withdrawn')),
  version integer NOT NULL DEFAULT 1,
  receipt_id bigint REFERENCES receipts(id),
  article_id text UNIQUE REFERENCES articles(id),
  reason text,
  reviewed_by text,
  reviewed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX upstream_reviews_status_idx ON upstream_reviews(status, updated_at DESC);
