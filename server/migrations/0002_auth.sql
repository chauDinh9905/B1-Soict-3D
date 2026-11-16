-- Tài khoản người dùng. Xem docs/BACKEND_PLAN.md mục 7.2.

CREATE TABLE users (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email             text NOT NULL,
  password_hash     text,                        -- NULL nếu chỉ đăng nhập bằng Google
  display_name      text,
  role              text NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  email_verified_at timestamptz,
  last_login_at     timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);
-- Không phân biệt hoa/thường. App cũng trim + lowercase trước khi lưu.
CREATE UNIQUE INDEX users_email_lower_uq ON users (lower(email));

CREATE TABLE oauth_accounts (                    -- giai đoạn B: đăng nhập Google
  provider         text NOT NULL,
  provider_user_id text NOT NULL,                -- 'sub' trong ID token, KHÔNG dùng email làm khóa
  user_id          uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at       timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (provider, provider_user_id)
);

CREATE TABLE auth_tokens (                       -- giai đoạn B: xác thực email, đặt lại mật khẩu
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose    text NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
  token_hash text NOT NULL UNIQUE,               -- sha256 của token; token gốc chỉ nằm trong email
  expires_at timestamptz NOT NULL,
  used_at    timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX auth_tokens_user_idx ON auth_tokens (user_id, purpose);

CREATE TABLE login_events (
  id         bigserial PRIMARY KEY,
  user_id    uuid REFERENCES users(id) ON DELETE SET NULL,
  email      text,
  success    boolean NOT NULL,
  reason     text,                               -- 'ok', 'bad_password', 'unknown_email'
  ip         inet,
  user_agent text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX login_events_created_idx ON login_events (created_at);

CREATE TABLE outbox (                            -- giai đoạn B: worker gửi email
  id         bigserial PRIMARY KEY,
  kind       text NOT NULL,
  payload    jsonb NOT NULL,
  attempts   integer NOT NULL DEFAULT 0,
  run_after  timestamptz NOT NULL DEFAULT now(),
  done_at    timestamptz,
  last_error text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX outbox_pending_idx ON outbox (run_after) WHERE done_at IS NULL;

ALTER TABLE feedback ADD COLUMN user_id uuid REFERENCES users(id) ON DELETE SET NULL;
