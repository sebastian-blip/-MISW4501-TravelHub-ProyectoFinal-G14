-- Tokens de push por dispositivo. Una fila por (usuario, token); un mismo
-- token sólo puede pertenecer a un user_id activo a la vez (es lo que
-- emite FCM/APNs por instalación + cuenta).

DROP TABLE IF EXISTS device_tokens;

CREATE TABLE device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    platform VARCHAR(16) NOT NULL CHECK (platform IN ('android', 'ios', 'web')),
    app_version VARCHAR(32),
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, token)
);

CREATE INDEX device_tokens_user_id_idx ON device_tokens (user_id);
CREATE INDEX device_tokens_token_idx ON device_tokens (token);
