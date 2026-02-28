CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS hotels (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    city        VARCHAR(100) NOT NULL,
    country     VARCHAR(3)   NOT NULL,
    address     TEXT         NOT NULL,
    stars       INTEGER      DEFAULT 3,
    active      BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS rooms (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id         UUID           NOT NULL REFERENCES hotels(id),
    room_type        VARCHAR(50)    NOT NULL,
    price_per_night  NUMERIC(10, 2) NOT NULL,
    capacity         INTEGER        DEFAULT 2,
    available        BOOLEAN        DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS reservations (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_id     UUID           NOT NULL,
    room_id      UUID           NOT NULL,
    user_id      UUID           NOT NULL,
    check_in     DATE           NOT NULL,
    check_out    DATE           NOT NULL,
    total_price  NUMERIC(10, 2) NOT NULL,
    status       VARCHAR(50)    DEFAULT 'pending',
    created_at   TIMESTAMP      DEFAULT NOW(),
    updated_at   TIMESTAMP      DEFAULT NOW()
);

INSERT INTO hotels (name, city, country, address, stars, active, created_at) VALUES
('Hotel Bogotá Plaza', 'Bogotá',   'COL', 'Cra 7 # 32-16',         5, true, NOW()),
('Casa Andina',        'Lima',     'PER', 'Av. La Paz 463',         4, true, NOW()),
('Hotel Dann Carlton', 'Medellín', 'COL', 'Calle 1A Sur # 43A-98', 5, true, NOW());

INSERT INTO rooms (hotel_id, room_type, price_per_night, capacity)
SELECT id, 'double', 120.00, 2 FROM hotels WHERE name = 'Hotel Bogotá Plaza';

INSERT INTO rooms (hotel_id, room_type, price_per_night, capacity)
SELECT id, 'suite', 250.00, 4 FROM hotels WHERE name = 'Hotel Bogotá Plaza';

INSERT INTO rooms (hotel_id, room_type, price_per_night, capacity)
SELECT id, 'single', 80.00, 1 FROM hotels WHERE name = 'Casa Andina';
SELECT id, 'single', 80.00, 1 FROM hotels WHERE name = 'Casa Andina';