-- ============================================
-- DATA MODEL - TRAVELHUB
-- PostgreSQL Database Schema
-- ============================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- MODULE: USER MANAGEMENT & AUTHENTICATION
-- ============================================

CREATE TABLE countries (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code          VARCHAR(3)   NOT NULL UNIQUE, -- ISO 3166-1 alpha-3
    name          VARCHAR(100) NOT NULL,
    currency_code VARCHAR(3)   NOT NULL,        -- USD, COP, ARS, CLP, PEN, MXN
    active        BOOLEAN      DEFAULT true,
    created_at    TIMESTAMP    DEFAULT NOW(),
    updated_at    TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE users (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email          VARCHAR(255) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    phone          VARCHAR(20),
    country_id     UUID REFERENCES countries(id),
    user_type      VARCHAR(50)  NOT NULL, -- 'traveler', 'hotel_admin', 'agency', 'admin'
    email_verified BOOLEAN      DEFAULT false,
    mfa_enabled    BOOLEAN      DEFAULT false,
    active         BOOLEAN      DEFAULT true,
    created_at     TIMESTAMP    DEFAULT NOW(),
    updated_at     TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE user_sessions (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID         NOT NULL REFERENCES users(id),
    token      VARCHAR(500) NOT NULL UNIQUE,
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP    NOT NULL,
    created_at TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL, -- 'login', 'reservation_created', 'payment_processed', etc.
    entity_type VARCHAR(50),           -- 'reservation', 'payment', 'hotel', etc.
    entity_id   UUID,
    ip_address  VARCHAR(45),
    details     JSONB,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- MODULE: HOTELS & PROPERTIES
-- ============================================

CREATE TABLE hotels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    address         TEXT         NOT NULL,
    city            VARCHAR(100) NOT NULL,
    country_id      UUID         NOT NULL REFERENCES countries(id),
    latitude        DECIMAL(10, 8),
    longitude       DECIMAL(11, 8),
    phone           VARCHAR(20),
    email           VARCHAR(255),
    stars           INTEGER      DEFAULT 3,
    rating          DECIMAL(2, 1),           -- 0.0 to 5.0
    total_reviews   INTEGER      DEFAULT 0,
    check_in_time   TIME         DEFAULT '15:00:00',
    check_out_time  TIME         DEFAULT '11:00:00',
    owner_user_id   UUID REFERENCES users(id),
    pms_provider    VARCHAR(100),            -- 'Hotelbeds', 'TravelClick', 'RoomRaccoon', etc.
    pms_hotel_code  VARCHAR(100),
    active          BOOLEAN      DEFAULT true,
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE hotel_amenities (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id   UUID         NOT NULL REFERENCES hotels(id),
    name       VARCHAR(100) NOT NULL, -- 'wifi', 'pool', 'parking', 'breakfast', 'gym', etc.
    icon       VARCHAR(50),
    created_at TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE hotel_images (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id   UUID         NOT NULL REFERENCES hotels(id),
    url        TEXT         NOT NULL,
    alt_text   VARCHAR(255),
    sort_order INTEGER      DEFAULT 0,
    image_type VARCHAR(50)  DEFAULT 'gallery', -- 'main', 'gallery', 'room', 'exterior'
    created_at TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE hotel_reviews (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id            UUID         NOT NULL REFERENCES hotels(id),
    user_id             UUID         NOT NULL REFERENCES users(id),
    reservation_id      UUID,
    overall_rating      DECIMAL(2, 1) NOT NULL, -- 1.0 to 5.0
    cleanliness_rating  DECIMAL(2, 1),
    service_rating      DECIMAL(2, 1),
    location_rating     DECIMAL(2, 1),
    value_rating        DECIMAL(2, 1),
    comment             TEXT,
    response            TEXT,            -- hotel response to review
    created_at          TIMESTAMP    DEFAULT NOW()
);

-- ============================================
-- MODULE: ROOMS & INVENTORY
-- ============================================

CREATE TABLE room_types (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        UUID           NOT NULL REFERENCES hotels(id),
    name            VARCHAR(100)   NOT NULL, -- 'Standard', 'Deluxe', 'Suite', etc.
    description     TEXT,
    base_price      DECIMAL(10, 2) NOT NULL,
    max_capacity    INTEGER        DEFAULT 2,
    bed_type        VARCHAR(50),             -- 'king', 'queen', 'twin', 'double'
    size_sqm        DECIMAL(5, 1),
    total_units     INTEGER        DEFAULT 1,
    active          BOOLEAN        DEFAULT true,
    created_at      TIMESTAMP      DEFAULT NOW(),
    updated_at      TIMESTAMP      DEFAULT NOW()
);

CREATE TABLE room_amenities (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID         NOT NULL REFERENCES room_types(id),
    name         VARCHAR(100) NOT NULL, -- 'tv', 'minibar', 'balcony', 'ocean_view', 'ac', etc.
    icon         VARCHAR(50),
    created_at   TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE room_images (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id UUID      NOT NULL REFERENCES room_types(id),
    url          TEXT      NOT NULL,
    alt_text     VARCHAR(255),
    sort_order   INTEGER   DEFAULT 0,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE inventory_calendar (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_type_id      UUID           NOT NULL REFERENCES room_types(id),
    date              DATE           NOT NULL,
    available_units   INTEGER        NOT NULL DEFAULT 0,
    price_per_night   DECIMAL(10, 2) NOT NULL,
    currency_code     VARCHAR(3)     NOT NULL DEFAULT 'USD',
    minimum_stay      INTEGER        DEFAULT 1,
    last_synced_at    TIMESTAMP,
    created_at        TIMESTAMP      DEFAULT NOW(),
    updated_at        TIMESTAMP      DEFAULT NOW(),
    UNIQUE (room_type_id, date)
);

CREATE TABLE rate_plans (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        UUID           NOT NULL REFERENCES hotels(id),
    name            VARCHAR(100)   NOT NULL, -- 'Early Bird 20%', 'Weekend Special', etc.
    discount_pct    DECIMAL(5, 2)  DEFAULT 0,
    valid_from      DATE,
    valid_to        DATE,
    minimum_stay    INTEGER        DEFAULT 1,
    refundable      BOOLEAN        DEFAULT true,
    active          BOOLEAN        DEFAULT true,
    created_at      TIMESTAMP      DEFAULT NOW()
);

CREATE TABLE special_offers (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id     UUID           NOT NULL REFERENCES hotels(id),
    room_type_id UUID REFERENCES room_types(id),
    title        VARCHAR(255)   NOT NULL,
    description  TEXT,
    discount_pct DECIMAL(5, 2)  NOT NULL,
    valid_from   DATE           NOT NULL,
    valid_to     DATE           NOT NULL,
    active       BOOLEAN        DEFAULT true,
    created_at   TIMESTAMP      DEFAULT NOW()
);

-- ============================================
-- MODULE: RESERVATIONS & BOOKINGS
-- ============================================

CREATE TABLE shopping_carts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID      NOT NULL REFERENCES users(id),
    room_type_id    UUID      NOT NULL REFERENCES room_types(id),
    check_in        DATE      NOT NULL,
    check_out       DATE      NOT NULL,
    guests          INTEGER   DEFAULT 1,
    hold_expires_at TIMESTAMP NOT NULL, -- 15-minute hold
    status          VARCHAR(50) DEFAULT 'active', -- 'active', 'expired', 'converted'
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reservations (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id              UUID           REFERENCES users(id),
    -- Usuario (viajero) bajo cuyo perfil se gestiona la reserva cuando otra persona reserva; opcional
    user_guest_id        UUID           REFERENCES users(id),
    hotel_id             UUID           NOT NULL REFERENCES hotels(id),
    room_type_id         UUID           NOT NULL REFERENCES room_types(id),
    cart_id              UUID REFERENCES shopping_carts(id),
    check_in             DATE           NOT NULL,
    check_out            DATE           NOT NULL,
    guests               INTEGER        DEFAULT 1,
    base_price           DECIMAL(10, 2) NOT NULL,
    taxes                DECIMAL(10, 2) DEFAULT 0,
    discounts            DECIMAL(10, 2) DEFAULT 0,
    total_price          DECIMAL(10, 2) NOT NULL,
    currency_code        VARCHAR(3)     NOT NULL DEFAULT 'USD',
    status               VARCHAR(50)    DEFAULT 'pending',
    -- 'pending', 'confirmed', 'cancelled', 'completed', 'no_show'
    cancellation_policy  VARCHAR(50),   -- 'non_refundable', 'partial', 'full'
    special_requests     TEXT,
    confirmation_code    VARCHAR(20)    UNIQUE,
    created_at           TIMESTAMP      DEFAULT NOW(),
    updated_at           TIMESTAMP      DEFAULT NOW()
);

CREATE INDEX idx_reservations_user_guest_id ON reservations (user_guest_id);

CREATE TABLE reservation_guests (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id UUID         NOT NULL REFERENCES reservations(id),
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    document_type  VARCHAR(50),  -- 'passport', 'id_card', 'driver_license'
    document_number VARCHAR(50),
    nationality    VARCHAR(3),
    is_primary     BOOLEAN      DEFAULT false,
    created_at     TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE reservation_status_history (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id UUID         NOT NULL REFERENCES reservations(id),
    previous_status VARCHAR(50),
    new_status     VARCHAR(50)  NOT NULL,
    changed_by     UUID REFERENCES users(id),
    reason         TEXT,
    ip_address     VARCHAR(45),
    created_at     TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE check_ins (
    id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id UUID        NOT NULL REFERENCES reservations(id) UNIQUE,
    qr_code        VARCHAR(255) NOT NULL UNIQUE,
    room_number    VARCHAR(20),
    checked_in_at  TIMESTAMP,
    checked_out_at TIMESTAMP,
    status         VARCHAR(50) DEFAULT 'pending', -- 'pending', 'checked_in', 'checked_out'
    created_at     TIMESTAMP   DEFAULT NOW(),
    updated_at     TIMESTAMP   DEFAULT NOW()
);

-- ============================================
-- MODULE: PAYMENTS & TRANSACTIONS
-- ============================================

CREATE TABLE payment_providers (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(100) NOT NULL, -- 'Stripe', 'MercadoPago', 'PayPal', 'OpenPay'
    country_id   UUID REFERENCES countries(id), -- NULL = global
    active       BOOLEAN      DEFAULT true,
    created_at   TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE payments (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reservation_id      UUID           NOT NULL REFERENCES reservations(id),
    provider_id         UUID           NOT NULL REFERENCES payment_providers(id),
    amount              DECIMAL(10, 2) NOT NULL,
    currency_code       VARCHAR(3)     NOT NULL DEFAULT 'USD',
    status              VARCHAR(50)    DEFAULT 'pending',
    -- 'pending', 'processing', 'completed', 'failed', 'refunded', 'partially_refunded'
    payment_token       VARCHAR(255),  -- provider token, never raw card data (PCI-DSS)
    provider_payment_id VARCHAR(255),  -- external ID from payment provider
    failure_reason      TEXT,
    refund_amount       DECIMAL(10, 2),
    refunded_at         TIMESTAMP,
    processed_at        TIMESTAMP,
    created_at          TIMESTAMP      DEFAULT NOW(),
    updated_at          TIMESTAMP      DEFAULT NOW()
);

CREATE TABLE payment_transactions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id          UUID           NOT NULL REFERENCES payments(id),
    type                VARCHAR(50)    NOT NULL, -- 'charge', 'refund', 'chargeback'
    amount              DECIMAL(10, 2) NOT NULL,
    status              VARCHAR(50)    NOT NULL,
    provider_tx_id      VARCHAR(255),
    fraud_score         DECIMAL(5, 2),           -- 0.0 to 100.0
    three_ds_verified   BOOLEAN        DEFAULT false,
    created_at          TIMESTAMP      DEFAULT NOW()
);

-- ============================================
-- MODULE: PMS INTEGRATION
-- ============================================

CREATE TABLE pms_sync_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        UUID         NOT NULL REFERENCES hotels(id),
    pms_provider    VARCHAR(100) NOT NULL,
    sync_type       VARCHAR(50)  NOT NULL, -- 'availability', 'rates', 'reservations'
    status          VARCHAR(50)  NOT NULL, -- 'success', 'failed', 'partial'
    records_synced  INTEGER      DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMP    NOT NULL,
    completed_at    TIMESTAMP,
    created_at      TIMESTAMP    DEFAULT NOW()
);

-- ============================================
-- MODULE: NOTIFICATIONS & COMMUNICATIONS
-- ============================================

CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID         NOT NULL REFERENCES users(id),
    type            VARCHAR(50)  NOT NULL, -- 'email', 'push', 'sms'
    title           VARCHAR(255) NOT NULL,
    body            TEXT         NOT NULL,
    related_entity  VARCHAR(50),           -- 'reservation', 'payment', 'check_in'
    entity_id       UUID,
    sent_at         TIMESTAMP,
    read_at         TIMESTAMP,
    status          VARCHAR(50)  DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    created_at      TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE email_templates (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name       VARCHAR(100) NOT NULL UNIQUE, -- 'reservation_confirmed', 'payment_receipt', etc.
    subject    VARCHAR(255) NOT NULL,
    body_html  TEXT         NOT NULL,
    body_text  TEXT,
    language   VARCHAR(5)   DEFAULT 'es',
    active     BOOLEAN      DEFAULT true,
    created_at TIMESTAMP    DEFAULT NOW(),
    updated_at TIMESTAMP    DEFAULT NOW()
);

-- ============================================
-- MODULE: REPORTING & ANALYTICS
-- ============================================

CREATE TABLE revenue_reports (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id        UUID           NOT NULL REFERENCES hotels(id),
    period_start    DATE           NOT NULL,
    period_end      DATE           NOT NULL,
    total_revenue   DECIMAL(12, 2) NOT NULL,
    total_bookings  INTEGER        DEFAULT 0,
    currency_code   VARCHAR(3)     NOT NULL DEFAULT 'USD',
    generated_at    TIMESTAMP      DEFAULT NOW()
);

CREATE TABLE occupancy_reports (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id         UUID          NOT NULL REFERENCES hotels(id),
    report_date      DATE          NOT NULL,
    total_rooms      INTEGER       NOT NULL,
    occupied_rooms   INTEGER       DEFAULT 0,
    occupancy_rate   DECIMAL(5, 2) DEFAULT 0, -- percentage
    generated_at     TIMESTAMP     DEFAULT NOW(),
    UNIQUE (hotel_id, report_date)
);

CREATE TABLE currency_exchange_rates (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_currency VARCHAR(3)     NOT NULL,
    to_currency   VARCHAR(3)     NOT NULL,
    rate          DECIMAL(15, 6) NOT NULL,
    fetched_at    TIMESTAMP      NOT NULL,
    created_at    TIMESTAMP      DEFAULT NOW(),
    UNIQUE (from_currency, to_currency, fetched_at)
);

-- ============================================
-- MODULE: TOURS (FUTURE SCOPE)
-- ============================================

CREATE TABLE tours (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name         VARCHAR(255)   NOT NULL,
    description  TEXT,
    country_id   UUID           NOT NULL REFERENCES countries(id),
    city         VARCHAR(100),
    price        DECIMAL(10, 2) NOT NULL,
    currency_code VARCHAR(3)    NOT NULL DEFAULT 'USD',
    duration_hrs INTEGER,
    active       BOOLEAN        DEFAULT true,
    created_at   TIMESTAMP      DEFAULT NOW(),
    updated_at   TIMESTAMP      DEFAULT NOW()
);

CREATE TABLE user_preferences (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID NOT NULL REFERENCES users(id) UNIQUE,
    preferred_currency VARCHAR(3) DEFAULT 'USD',
    preferred_language VARCHAR(5) DEFAULT 'es',
    notifications_email BOOLEAN DEFAULT true,
    notifications_push  BOOLEAN DEFAULT true,
    created_at         TIMESTAMP DEFAULT NOW(),
    updated_at         TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- SEED DATA: Countries
-- ============================================

INSERT INTO countries (code, name, currency_code) VALUES
    ('COL', 'Colombia',  'COP'),
    ('PER', 'Perú',      'PEN'),
    ('ECU', 'Ecuador',   'USD'),
    ('MEX', 'México',    'MXN'),
    ('CHL', 'Chile',     'CLP'),
    ('ARG', 'Argentina', 'ARS');