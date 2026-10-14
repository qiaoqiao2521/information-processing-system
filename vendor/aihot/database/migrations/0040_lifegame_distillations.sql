CREATE TABLE lifegame_distillations (
  id text PRIMARY KEY,
  request_id text NOT NULL UNIQUE,
  item_id text NOT NULL,
  title text NOT NULL,
  source text NOT NULL,
  source_url text NOT NULL,
  fingerprint text NOT NULL,
  basis text NOT NULL CHECK (basis IN ('full_text','public_summary')),
  truncated boolean NOT NULL DEFAULT false,
  model text NOT NULL,
  conclusion text NOT NULL,
  key_points jsonb NOT NULL CHECK (jsonb_typeof(key_points) = 'array' AND jsonb_array_length(key_points) = 3),
  entities jsonb NOT NULL DEFAULT '[]' CHECK (jsonb_typeof(entities) = 'array' AND jsonb_array_length(entities) <= 40),
  status text NOT NULL DEFAULT 'draft' CHECK (status = 'draft'),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX lifegame_distillations_created_idx ON lifegame_distillations(created_at DESC);
