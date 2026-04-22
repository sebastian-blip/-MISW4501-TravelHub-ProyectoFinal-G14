-- SQL para crear la tabla de reservaciones

-- Eliminar tabla si existe
DROP TABLE IF EXISTS reservations;

CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    hotel_id UUID NOT NULL,
    room_type_id UUID NOT NULL,
    cart_id UUID,
    
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guests INTEGER DEFAULT 1,
    
    base_price DECIMAL(10, 2) NOT NULL,
    taxes DECIMAL(10, 2) DEFAULT 0,
    discounts DECIMAL(10, 2) DEFAULT 0,
    total_price DECIMAL(10, 2) NOT NULL,
    currency_code VARCHAR(3) DEFAULT 'USD',
    
    status VARCHAR(50) DEFAULT 'pending',
    cancellation_policy VARCHAR(50),
    special_requests TEXT,
    confirmation_code VARCHAR(20) UNIQUE,
    
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Crear índices
CREATE INDEX idx_reservations_user_id ON reservations(user_id);
CREATE INDEX idx_reservations_hotel_id ON reservations(hotel_id);
CREATE INDEX idx_reservations_room_type_id ON reservations(room_type_id);
CREATE INDEX idx_reservations_cart_id ON reservations(cart_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_confirmation_code ON reservations(confirmation_code);
