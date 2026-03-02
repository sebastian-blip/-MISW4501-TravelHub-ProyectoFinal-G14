-- PoC-5 GDPR: databases for User Service, Reader, Reservations, Analytics, Audit
-- Run once per database or use one DB with schemas (we use one DB for simplicity)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User Service (writer): users + audit events (T0 and completado por consumidor)
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       VARCHAR(255) NOT NULL,
    name        VARCHAR(255),
    anonymized  BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMP    DEFAULT NOW(),
    updated_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_events (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type   VARCHAR(50)  NOT NULL,  -- 'solicitud_olvido' | 'completado'
    user_id      UUID         NOT NULL,
    consumer_id  VARCHAR(50),            -- 'reader' | 'reservations' | 'analytics' (solo para completado)
    timestamp    TIMESTAMP    DEFAULT NOW(),
    payload      JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type);

-- Reader: read model (proyección de usuarios para consultas)
CREATE TABLE IF NOT EXISTS user_read_model (
    id          UUID PRIMARY KEY,
    email       VARCHAR(255),
    name        VARCHAR(255),
    anonymized  BOOLEAN      DEFAULT FALSE,
    updated_at  TIMESTAMP    DEFAULT NOW()
);

-- Reservations: reservas con referencia a usuario (anonimizar user_id, no borrar fila)
CREATE TABLE IF NOT EXISTS reservations (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id      UUID         NOT NULL,
    hotel_id     UUID         NOT NULL,
    room_id      UUID         NOT NULL,
    check_in     DATE         NOT NULL,
    check_out    DATE         NOT NULL,
    total_price  NUMERIC(10, 2),
    status       VARCHAR(50)   DEFAULT 'confirmed',
    created_at   TIMESTAMP    DEFAULT NOW(),
    updated_at   TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reservations_user_id ON reservations(user_id);

-- Analytics: tabla mínima de "reporte" con user_id (anonimizar en consumidor)
CREATE TABLE IF NOT EXISTS analytics_user_activity (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID         NOT NULL,
    event_type  VARCHAR(50)   NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMP    DEFAULT NOW(),
    anonymized  BOOLEAN      DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_analytics_user_id ON analytics_user_activity(user_id);

-- Seed one user for testing
INSERT INTO users (id, email, name, anonymized) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'test@travelhub.com', 'Test User', FALSE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_read_model (id, email, name, anonymized) VALUES
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'test@travelhub.com', 'Test User', FALSE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO reservations (user_id, hotel_id, room_id, check_in, check_out, total_price, status)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, uuid_generate_v4(), uuid_generate_v4(), CURRENT_DATE, CURRENT_DATE + 2, 150.00, 'confirmed'
WHERE NOT EXISTS (SELECT 1 FROM reservations LIMIT 1);

INSERT INTO analytics_user_activity (user_id, event_type, payload, anonymized)
SELECT 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'::uuid, 'page_view', '{"page": "home"}', FALSE
WHERE NOT EXISTS (SELECT 1 FROM analytics_user_activity LIMIT 1);
