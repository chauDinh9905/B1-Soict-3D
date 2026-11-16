-- Bảng nội dung, chuyển từ SQLite (src/db/schema.sql cũ) sang PostgreSQL.
-- Dữ liệu nạp bằng `npm run seed` từ web/public/data – không nhập tay.

CREATE TABLE buildings (
  id           text PRIMARY KEY,                 -- 'b1', 'c1'...
  name         text NOT NULL,
  description  text,
  model        text NOT NULL,                    -- đường dẫn .glb trong web/public
  lat          double precision NOT NULL,
  lon          double precision NOT NULL,
  rotation_deg double precision NOT NULL DEFAULT 0,
  placeholder  jsonb,                            -- [w, h, d]
  views        jsonb NOT NULL DEFAULT '[]',      -- ["Cam_Ref", ...]
  enabled      boolean NOT NULL DEFAULT true,
  sort_order   integer NOT NULL DEFAULT 0
);

CREATE TABLE pois (
  id          text PRIMARY KEY,
  building_id text NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
  title       text NOT NULL,
  text        text,
  image       text,
  x double precision NOT NULL,                   -- tọa độ cục bộ của tòa nhà (Three.js, mét)
  y double precision NOT NULL,
  z double precision NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX pois_building_idx ON pois (building_id);

CREATE TABLE feedback (
  id         bigserial PRIMARY KEY,
  name       text,
  message    text NOT NULL,
  poi_id     text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE visits (
  day   date PRIMARY KEY,
  count integer NOT NULL DEFAULT 0
);
