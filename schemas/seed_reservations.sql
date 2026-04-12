-- ============================================
-- SEED DATA: TravelHub - Reservas
-- ============================================
-- Prerequisito: seed_hotels.sql ejecutado previamente
-- Cubre: usuarios viajeros, carritos, reservas,
--        huéspedes, historial de estados, check-ins,
--        pagos, transacciones y notificaciones

-- ============================================
-- 1. USUARIOS VIAJEROS
-- ============================================

INSERT INTO users (id, email, password_hash, first_name, last_name, phone, country_id, user_type, email_verified, active) VALUES
    (
        'd1000000-0000-0000-0000-000000000001',
        'juan.perez@gmail.com',
        '$2b$12$placeholderHashJuan',
        'Juan', 'Pérez', '+573105678901',
        (SELECT id FROM countries WHERE code = 'COL'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000002',
        'sofia.ramirez@hotmail.com',
        '$2b$12$placeholderHashSofia',
        'Sofía', 'Ramírez', '+51987001122',
        (SELECT id FROM countries WHERE code = 'PER'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000003',
        'diego.torres@outlook.com',
        '$2b$12$placeholderHashDiego',
        'Diego', 'Torres', '+5215567891234',
        (SELECT id FROM countries WHERE code = 'MEX'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000004',
        'valentina.mora@yahoo.com',
        '$2b$12$placeholderHashValentina',
        'Valentina', 'Mora', '+56922334455',
        (SELECT id FROM countries WHERE code = 'CHL'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000005',
        'martin.lopez@gmail.com',
        '$2b$12$placeholderHashMartin',
        'Martín', 'López', '+541156789012',
        (SELECT id FROM countries WHERE code = 'ARG'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000006',
        'camila.vega@gmail.com',
        '$2b$12$placeholderHashCamila',
        'Camila', 'Vega', '+593987654321',
        (SELECT id FROM countries WHERE code = 'ECU'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000007',
        'andres.silva@empresa.com',
        '$2b$12$placeholderHashAndres',
        'Andrés', 'Silva', '+573209876543',
        (SELECT id FROM countries WHERE code = 'COL'),
        'traveler', true, true
    ),
    (
        'd1000000-0000-0000-0000-000000000008',
        'isabella.castro@gmail.com',
        '$2b$12$placeholderHashIsabella',
        'Isabella', 'Castro', '+51955443322',
        (SELECT id FROM countries WHERE code = 'PER'),
        'traveler', true, true
    );

-- ============================================
-- 2. USER PREFERENCES
-- ============================================

INSERT INTO user_preferences (user_id, preferred_currency, preferred_language, notifications_email, notifications_push) VALUES
    ('d1000000-0000-0000-0000-000000000001', 'COP', 'es', true,  true),
    ('d1000000-0000-0000-0000-000000000002', 'PEN', 'es', true,  true),
    ('d1000000-0000-0000-0000-000000000003', 'MXN', 'es', true,  false),
    ('d1000000-0000-0000-0000-000000000004', 'CLP', 'es', true,  true),
    ('d1000000-0000-0000-0000-000000000005', 'ARS', 'es', false, true),
    ('d1000000-0000-0000-0000-000000000006', 'USD', 'es', true,  true),
    ('d1000000-0000-0000-0000-000000000007', 'USD', 'es', true,  true),
    ('d1000000-0000-0000-0000-000000000008', 'USD', 'es', true,  false);

-- ============================================
-- 3. PAYMENT PROVIDERS
-- ============================================

INSERT INTO payment_providers (id, name, country_id, active) VALUES
    ('e1000000-0000-0000-0000-000000000001', 'Stripe',       NULL,                                          true),
    ('e1000000-0000-0000-0000-000000000002', 'MercadoPago',  (SELECT id FROM countries WHERE code = 'ARG'), true),
    ('e1000000-0000-0000-0000-000000000003', 'MercadoPago',  (SELECT id FROM countries WHERE code = 'COL'), true),
    ('e1000000-0000-0000-0000-000000000004', 'OpenPay',      (SELECT id FROM countries WHERE code = 'MEX'), true),
    ('e1000000-0000-0000-0000-000000000005', 'PayPal',       NULL,                                          true);

-- ============================================
-- 4. SHOPPING CARTS
-- Mezcla de estados: converted, expired, active
-- ============================================

INSERT INTO shopping_carts (id, user_id, room_type_id, check_in, check_out, guests, hold_expires_at, status) VALUES

    -- Convertidos a reserva (el hold ya pasó, status = converted)
    (
        'f1000000-0000-0000-0000-000000000001',
        'd1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000102',  -- Deluxe Bogotá
        CURRENT_DATE + 10, CURRENT_DATE + 13,
        2,
        NOW() - INTERVAL '2 days',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000002',
        'd1000000-0000-0000-0000-000000000002',
        'c1000000-0000-0000-0000-000000000201',  -- Ocean Room Lima
        CURRENT_DATE + 15, CURRENT_DATE + 20,
        2,
        NOW() - INTERVAL '3 days',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000003',
        'd1000000-0000-0000-0000-000000000003',
        'c1000000-0000-0000-0000-000000000402',  -- Superior Zócalo CDMX
        CURRENT_DATE + 5,  CURRENT_DATE + 8,
        3,
        NOW() - INTERVAL '1 day',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000004',
        'd1000000-0000-0000-0000-000000000004',
        'c1000000-0000-0000-0000-000000000502',  -- Pool View Santiago
        CURRENT_DATE + 20, CURRENT_DATE + 25,
        2,
        NOW() - INTERVAL '5 days',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000005',
        'd1000000-0000-0000-0000-000000000005',
        'c1000000-0000-0000-0000-000000000602',  -- Suite Palermo BA
        CURRENT_DATE + 7,  CURRENT_DATE + 10,
        2,
        NOW() - INTERVAL '1 day',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000006',
        'd1000000-0000-0000-0000-000000000006',
        'c1000000-0000-0000-0000-000000000302',  -- Presidencial Quito
        CURRENT_DATE + 30, CURRENT_DATE + 34,
        2,
        NOW() - INTERVAL '4 hours',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000007',
        'd1000000-0000-0000-0000-000000000007',
        'c1000000-0000-0000-0000-000000000103',  -- Suite Ejecutiva Bogotá
        CURRENT_DATE + 45, CURRENT_DATE + 48,
        4,
        NOW() - INTERVAL '2 hours',
        'converted'
    ),
    (
        'f1000000-0000-0000-0000-000000000008',
        'd1000000-0000-0000-0000-000000000008',
        'c1000000-0000-0000-0000-000000000203',  -- Penthouse Lima
        CURRENT_DATE + 60, CURRENT_DATE + 65,
        4,
        NOW() - INTERVAL '1 day',
        'converted'
    ),
    -- Expirado (usuario abandonó el carrito)
    (
        'f1000000-0000-0000-0000-000000000009',
        'd1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000503',  -- Suite Noi Santiago
        CURRENT_DATE + 30, CURRENT_DATE + 33,
        2,
        NOW() - INTERVAL '1 hour',
        'expired'
    ),
    -- Activo (hold vigente, 15 minutos desde ahora)
    (
        'f1000000-0000-0000-0000-000000000010',
        'd1000000-0000-0000-0000-000000000003',
        'c1000000-0000-0000-0000-000000000101',  -- Estándar Bogotá
        CURRENT_DATE + 14, CURRENT_DATE + 16,
        1,
        NOW() + INTERVAL '15 minutes',
        'active'
    );

-- ============================================
-- 5. RESERVATIONS
-- Variedad de estados: confirmed, pending,
-- cancelled, completed
-- ============================================

INSERT INTO reservations (
    id, user_id, hotel_id, room_type_id, cart_id,
    check_in, check_out, guests,
    base_price, taxes, discounts, total_price, currency_code,
    status, cancellation_policy, special_requests, confirmation_code
) VALUES

    -- R01: Confirmada - Juan en Bogotá Deluxe (3 noches x $145 + weekend premium)
    (
        'a2000000-0000-0000-0000-000000000001',
        'd1000000-0000-0000-0000-000000000001',
        'b1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000102',
        'f1000000-0000-0000-0000-000000000001',
        CURRENT_DATE + 10, CURRENT_DATE + 13,
        2,
        435.00, 78.30, 43.50, 469.80, 'USD',
        'confirmed', 'partial',
        'Piso alto si es posible, llegamos tarde en la noche.',
        'TH-2026-00001'
    ),

    -- R02: Confirmada - Sofía en Lima Ocean Room (5 noches)
    (
        'a2000000-0000-0000-0000-000000000002',
        'd1000000-0000-0000-0000-000000000002',
        'b1000000-0000-0000-0000-000000000002',
        'c1000000-0000-0000-0000-000000000201',
        'f1000000-0000-0000-0000-000000000002',
        CURRENT_DATE + 15, CURRENT_DATE + 20,
        2,
        1100.00, 198.00, 110.00, 1188.00, 'USD',
        'confirmed', 'full',
        'Aniversario de bodas, solicito arreglo floral en la habitación.',
        'TH-2026-00002'
    ),

    -- R03: Confirmada - Diego en CDMX Superior Zócalo (3 noches)
    (
        'a2000000-0000-0000-0000-000000000003',
        'd1000000-0000-0000-0000-000000000003',
        'b1000000-0000-0000-0000-000000000004',
        'c1000000-0000-0000-0000-000000000402',
        'f1000000-0000-0000-0000-000000000003',
        CURRENT_DATE + 5, CURRENT_DATE + 8,
        3,
        585.00, 105.30, 0.00, 690.30, 'USD',
        'confirmed', 'partial',
        'Cama adicional para niño de 8 años.',
        'TH-2026-00003'
    ),

    -- R04: Confirmada - Valentina en Santiago Pool View (5 noches)
    (
        'a2000000-0000-0000-0000-000000000004',
        'd1000000-0000-0000-0000-000000000004',
        'b1000000-0000-0000-0000-000000000005',
        'c1000000-0000-0000-0000-000000000502',
        'f1000000-0000-0000-0000-000000000004',
        CURRENT_DATE + 20, CURRENT_DATE + 25,
        2,
        1200.00, 216.00, 180.00, 1236.00, 'USD',
        'confirmed', 'partial',
        NULL,
        'TH-2026-00004'
    ),

    -- R05: Confirmada - Martín en Buenos Aires Suite Palermo (3 noches)
    (
        'a2000000-0000-0000-0000-000000000005',
        'd1000000-0000-0000-0000-000000000005',
        'b1000000-0000-0000-0000-000000000006',
        'c1000000-0000-0000-0000-000000000602',
        'f1000000-0000-0000-0000-000000000005',
        CURRENT_DATE + 7, CURRENT_DATE + 10,
        2,
        525.00, 94.50, 42.00, 577.50, 'USD',
        'confirmed', 'non_refundable',
        'Check-in tardío, llegamos después de las 22:00.',
        'TH-2026-00005'
    ),

    -- R06: Pendiente - Camila en Quito Presidencial (4 noches)
    (
        'a2000000-0000-0000-0000-000000000006',
        'd1000000-0000-0000-0000-000000000006',
        'b1000000-0000-0000-0000-000000000003',
        'c1000000-0000-0000-0000-000000000302',
        'f1000000-0000-0000-0000-000000000006',
        CURRENT_DATE + 30, CURRENT_DATE + 34,
        2,
        840.00, 151.20, 0.00, 991.20, 'USD',
        'pending', 'full',
        NULL,
        'TH-2026-00006'
    ),

    -- R07: Confirmada - Andrés en Bogotá Suite Ejecutiva (3 noches, viaje corporativo)
    (
        'a2000000-0000-0000-0000-000000000007',
        'd1000000-0000-0000-0000-000000000007',
        'b1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000103',
        'f1000000-0000-0000-0000-000000000007',
        CURRENT_DATE + 45, CURRENT_DATE + 48,
        4,
        840.00, 151.20, 84.00, 907.20, 'USD',
        'confirmed', 'partial',
        'Viaje corporativo. Factura a nombre de Empresa SAS NIT 900.123.456-7.',
        'TH-2026-00007'
    ),

    -- R08: Confirmada - Isabella en Lima Penthouse (5 noches)
    (
        'a2000000-0000-0000-0000-000000000008',
        'd1000000-0000-0000-0000-000000000008',
        'b1000000-0000-0000-0000-000000000002',
        'c1000000-0000-0000-0000-000000000203',
        'f1000000-0000-0000-0000-000000000008',
        CURRENT_DATE + 60, CURRENT_DATE + 65,
        4,
        4250.00, 765.00, 425.00, 4590.00, 'USD',
        'confirmed', 'partial',
        'Solicito decoración especial para celebración de cumpleaños.',
        'TH-2026-00008'
    ),

    -- R09: Cancelada - Juan (reserva anterior cancelada)
    (
        'a2000000-0000-0000-0000-000000000009',
        'd1000000-0000-0000-0000-000000000001',
        'b1000000-0000-0000-0000-000000000005',
        'c1000000-0000-0000-0000-000000000501',
        NULL,
        CURRENT_DATE - 5, CURRENT_DATE - 2,
        2,
        480.00, 86.40, 0.00, 566.40, 'USD',
        'cancelled', 'partial',
        NULL,
        'TH-2026-00009'
    ),

    -- R10: Completada - Sofía (estancia ya finalizada)
    (
        'a2000000-0000-0000-0000-000000000010',
        'd1000000-0000-0000-0000-000000000002',
        'b1000000-0000-0000-0000-000000000003',
        'c1000000-0000-0000-0000-000000000301',
        NULL,
        CURRENT_DATE - 10, CURRENT_DATE - 7,
        2,
        390.00, 70.20, 58.50, 401.70, 'USD',
        'completed', 'full',
        NULL,
        'TH-2026-00010'
    );

-- ============================================
-- 6. RESERVATION GUESTS (huéspedes por reserva)
-- ============================================

INSERT INTO reservation_guests (reservation_id, first_name, last_name, document_type, document_number, nationality, is_primary) VALUES
    -- R01 - Juan Pérez + acompañante
    ('a2000000-0000-0000-0000-000000000001', 'Juan',      'Pérez',    'id_card',  '1030456789', 'COL', true),
    ('a2000000-0000-0000-0000-000000000001', 'Laura',     'Pérez',    'id_card',  '1030456790', 'COL', false),

    -- R02 - Sofía Ramírez + pareja
    ('a2000000-0000-0000-0000-000000000002', 'Sofía',     'Ramírez',  'passport', 'PE12345678', 'PER', true),
    ('a2000000-0000-0000-0000-000000000002', 'Carlos',    'Ramírez',  'passport', 'PE12345679', 'PER', false),

    -- R03 - Diego Torres + familia
    ('a2000000-0000-0000-0000-000000000003', 'Diego',     'Torres',   'passport', 'MX98765432', 'MEX', true),
    ('a2000000-0000-0000-0000-000000000003', 'Patricia',  'Torres',   'passport', 'MX98765433', 'MEX', false),
    ('a2000000-0000-0000-0000-000000000003', 'Miguel',    'Torres',   'id_card',  'MEX-MENOR-01','MEX', false),

    -- R04 - Valentina Mora
    ('a2000000-0000-0000-0000-000000000004', 'Valentina', 'Mora',     'passport', 'CL55443322', 'CHL', true),
    ('a2000000-0000-0000-0000-000000000004', 'Roberto',   'Mora',     'passport', 'CL55443323', 'CHL', false),

    -- R05 - Martín López
    ('a2000000-0000-0000-0000-000000000005', 'Martín',   'López',    'id_card',  'ARG20304050', 'ARG', true),
    ('a2000000-0000-0000-0000-000000000005', 'Ana',       'López',    'id_card',  'ARG20304051', 'ARG', false),

    -- R06 - Camila Vega
    ('a2000000-0000-0000-0000-000000000006', 'Camila',    'Vega',     'passport', 'EC11223344', 'ECU', true),
    ('a2000000-0000-0000-0000-000000000006', 'Felipe',    'Vega',     'passport', 'EC11223345', 'ECU', false),

    -- R07 - Andrés Silva + equipo
    ('a2000000-0000-0000-0000-000000000007', 'Andrés',   'Silva',    'id_card',  '1020304050', 'COL', true),
    ('a2000000-0000-0000-0000-000000000007', 'Paula',     'Gómez',    'id_card',  '1020304051', 'COL', false),
    ('a2000000-0000-0000-0000-000000000007', 'Ricardo',   'Muñoz',    'id_card',  '1020304052', 'COL', false),
    ('a2000000-0000-0000-0000-000000000007', 'Natalia',   'Cruz',     'id_card',  '1020304053', 'COL', false),

    -- R08 - Isabella Castro + grupo
    ('a2000000-0000-0000-0000-000000000008', 'Isabella',  'Castro',   'passport', 'PE87654321', 'PER', true),
    ('a2000000-0000-0000-0000-000000000008', 'Gabriel',   'Castro',   'passport', 'PE87654322', 'PER', false),
    ('a2000000-0000-0000-0000-000000000008', 'Lucia',     'Castro',   'passport', 'PE87654323', 'PER', false),
    ('a2000000-0000-0000-0000-000000000008', 'Tomás',     'Castro',   'passport', 'PE87654324', 'PER', false),

    -- R09 - Juan (cancelada)
    ('a2000000-0000-0000-0000-000000000009', 'Juan',      'Pérez',    'id_card',  '1030456789', 'COL', true),
    ('a2000000-0000-0000-0000-000000000009', 'Laura',     'Pérez',    'id_card',  '1030456790', 'COL', false),

    -- R10 - Sofía (completada)
    ('a2000000-0000-0000-0000-000000000010', 'Sofía',     'Ramírez',  'passport', 'PE12345678', 'PER', true),
    ('a2000000-0000-0000-0000-000000000010', 'Carlos',    'Ramírez',  'passport', 'PE12345679', 'PER', false);

-- ============================================
-- 7. RESERVATION STATUS HISTORY
-- ============================================

INSERT INTO reservation_status_history (reservation_id, previous_status, new_status, changed_by, reason, ip_address) VALUES
    -- R01: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000001', NULL,        'pending',   'd1000000-0000-0000-0000-000000000001', 'Reserva creada',            '190.24.10.1'),
    ('a2000000-0000-0000-0000-000000000001', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','190.24.10.1'),

    -- R02: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000002', NULL,        'pending',   'd1000000-0000-0000-0000-000000000002', 'Reserva creada',            '186.33.45.2'),
    ('a2000000-0000-0000-0000-000000000002', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','186.33.45.2'),

    -- R03: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000003', NULL,        'pending',   'd1000000-0000-0000-0000-000000000003', 'Reserva creada',            '200.68.12.5'),
    ('a2000000-0000-0000-0000-000000000003', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','200.68.12.5'),

    -- R04: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000004', NULL,        'pending',   'd1000000-0000-0000-0000-000000000004', 'Reserva creada',            '191.102.3.8'),
    ('a2000000-0000-0000-0000-000000000004', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','191.102.3.8'),

    -- R05: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000005', NULL,        'pending',   'd1000000-0000-0000-0000-000000000005', 'Reserva creada',            '181.46.78.9'),
    ('a2000000-0000-0000-0000-000000000005', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','181.46.78.9'),

    -- R06: solo pending (pago aún no procesado)
    ('a2000000-0000-0000-0000-000000000006', NULL,        'pending',   'd1000000-0000-0000-0000-000000000006', 'Reserva creada',            '186.5.44.22'),

    -- R07: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000007', NULL,        'pending',   'd1000000-0000-0000-0000-000000000007', 'Reserva creada',            '181.57.8.10'),
    ('a2000000-0000-0000-0000-000000000007', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','181.57.8.10'),

    -- R08: pending -> confirmed
    ('a2000000-0000-0000-0000-000000000008', NULL,        'pending',   'd1000000-0000-0000-0000-000000000008', 'Reserva creada',            '186.33.45.3'),
    ('a2000000-0000-0000-0000-000000000008', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','186.33.45.3'),

    -- R09: pending -> confirmed -> cancelled
    ('a2000000-0000-0000-0000-000000000009', NULL,        'pending',   'd1000000-0000-0000-0000-000000000001', 'Reserva creada',            '190.24.10.1'),
    ('a2000000-0000-0000-0000-000000000009', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','190.24.10.1'),
    ('a2000000-0000-0000-0000-000000000009', 'confirmed', 'cancelled', 'd1000000-0000-0000-0000-000000000001', 'Cambio de planes del viajero','190.24.10.1'),

    -- R10: pending -> confirmed -> completed
    ('a2000000-0000-0000-0000-000000000010', NULL,        'pending',   'd1000000-0000-0000-0000-000000000002', 'Reserva creada',            '186.33.45.2'),
    ('a2000000-0000-0000-0000-000000000010', 'pending',   'confirmed', NULL,                                   'Pago procesado exitosamente','186.33.45.2'),
    ('a2000000-0000-0000-0000-000000000010', 'confirmed', 'completed', NULL,                                   'Check-out procesado',       '186.33.45.2');

-- ============================================
-- 8. CHECK-INS (solo reservas confirmadas/completadas)
-- ============================================

INSERT INTO check_ins (reservation_id, qr_code, room_number, checked_in_at, checked_out_at, status) VALUES
    -- R01 - Check-in pendiente (fecha futura)
    ('a2000000-0000-0000-0000-000000000001', 'QR-TH2026-00001-A8F3', '412',  NULL,                       NULL,                       'pending'),
    -- R02 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000002', 'QR-TH2026-00002-B7E2', '508',  NULL,                       NULL,                       'pending'),
    -- R03 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000003', 'QR-TH2026-00003-C6D1', '211',  NULL,                       NULL,                       'pending'),
    -- R04 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000004', 'QR-TH2026-00004-D5C0', '302',  NULL,                       NULL,                       'pending'),
    -- R05 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000005', 'QR-TH2026-00005-E4B9', '115',  NULL,                       NULL,                       'pending'),
    -- R07 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000007', 'QR-TH2026-00007-G2A7', '601',  NULL,                       NULL,                       'pending'),
    -- R08 - Check-in pendiente
    ('a2000000-0000-0000-0000-000000000008', 'QR-TH2026-00008-H1Z6', 'PH1',  NULL,                       NULL,                       'pending'),
    -- R10 - Check-in y check-out completados
    ('a2000000-0000-0000-0000-000000000010', 'QR-TH2026-00010-J9X4', '104',
     NOW() - INTERVAL '10 days',
     NOW() - INTERVAL '7 days',
     'checked_out');

-- ============================================
-- 9. PAYMENTS
-- ============================================

INSERT INTO payments (
    id, reservation_id, provider_id,
    amount, currency_code, status,
    payment_token, provider_payment_id,
    failure_reason, refund_amount, refunded_at, processed_at
) VALUES
    -- R01 - Pago completado (Stripe)
    (
        'b2000000-0000-0000-0000-000000000001',
        'a2000000-0000-0000-0000-000000000001',
        'e1000000-0000-0000-0000-000000000001',
        469.80, 'USD', 'completed',
        'tok_stripe_sandbox_R01_abc123',
        'pi_3ABC123DEF456GHI',
        NULL, NULL, NULL,
        NOW() - INTERVAL '2 days'
    ),
    -- R02 - Pago completado (Stripe)
    (
        'b2000000-0000-0000-0000-000000000002',
        'a2000000-0000-0000-0000-000000000002',
        'e1000000-0000-0000-0000-000000000001',
        1188.00, 'USD', 'completed',
        'tok_stripe_sandbox_R02_def456',
        'pi_3DEF456GHI789JKL',
        NULL, NULL, NULL,
        NOW() - INTERVAL '3 days'
    ),
    -- R03 - Pago completado (OpenPay - México)
    (
        'b2000000-0000-0000-0000-000000000003',
        'a2000000-0000-0000-0000-000000000003',
        'e1000000-0000-0000-0000-000000000004',
        690.30, 'USD', 'completed',
        'tok_openpay_sandbox_R03_ghi789',
        'op_ch_3GHI789JKL012MNO',
        NULL, NULL, NULL,
        NOW() - INTERVAL '1 day'
    ),
    -- R04 - Pago completado (Stripe)
    (
        'b2000000-0000-0000-0000-000000000004',
        'a2000000-0000-0000-0000-000000000004',
        'e1000000-0000-0000-0000-000000000001',
        1236.00, 'USD', 'completed',
        'tok_stripe_sandbox_R04_jkl012',
        'pi_3JKL012MNO345PQR',
        NULL, NULL, NULL,
        NOW() - INTERVAL '5 days'
    ),
    -- R05 - Pago completado (MercadoPago - Argentina)
    (
        'b2000000-0000-0000-0000-000000000005',
        'a2000000-0000-0000-0000-000000000005',
        'e1000000-0000-0000-0000-000000000002',
        577.50, 'USD', 'completed',
        'tok_mp_sandbox_R05_mno345',
        'mp_pay_3MNO345PQR678STU',
        NULL, NULL, NULL,
        NOW() - INTERVAL '1 day'
    ),
    -- R06 - Pago pendiente (reserva aún pendiente)
    (
        'b2000000-0000-0000-0000-000000000006',
        'a2000000-0000-0000-0000-000000000006',
        'e1000000-0000-0000-0000-000000000001',
        991.20, 'USD', 'pending',
        NULL, NULL, NULL, NULL, NULL, NULL
    ),
    -- R07 - Pago completado (Stripe - corporativo)
    (
        'b2000000-0000-0000-0000-000000000007',
        'a2000000-0000-0000-0000-000000000007',
        'e1000000-0000-0000-0000-000000000001',
        907.20, 'USD', 'completed',
        'tok_stripe_sandbox_R07_pqr678',
        'pi_3PQR678STU901VWX',
        NULL, NULL, NULL,
        NOW() - INTERVAL '2 hours'
    ),
    -- R08 - Pago completado (Stripe - premium)
    (
        'b2000000-0000-0000-0000-000000000008',
        'a2000000-0000-0000-0000-000000000008',
        'e1000000-0000-0000-0000-000000000001',
        4590.00, 'USD', 'completed',
        'tok_stripe_sandbox_R08_stu901',
        'pi_3STU901VWX234YZA',
        NULL, NULL, NULL,
        NOW() - INTERVAL '1 day'
    ),
    -- R09 - Pago reembolsado (reserva cancelada - política partial)
    (
        'b2000000-0000-0000-0000-000000000009',
        'a2000000-0000-0000-0000-000000000009',
        'e1000000-0000-0000-0000-000000000001',
        566.40, 'USD', 'partially_refunded',
        'tok_stripe_sandbox_R09_vwx234',
        'pi_3VWX234YZA567BCD',
        NULL, 283.20, NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '8 days'
    ),
    -- R10 - Pago completado (reserva finalizada)
    (
        'b2000000-0000-0000-0000-000000000010',
        'a2000000-0000-0000-0000-000000000010',
        'e1000000-0000-0000-0000-000000000001',
        401.70, 'USD', 'completed',
        'tok_stripe_sandbox_R10_yza567',
        'pi_3YZA567BCD890EFG',
        NULL, NULL, NULL,
        NOW() - INTERVAL '12 days'
    );

-- ============================================
-- 10. PAYMENT TRANSACTIONS
-- ============================================

INSERT INTO payment_transactions (payment_id, type, amount, status, provider_tx_id, fraud_score, three_ds_verified) VALUES
    ('b2000000-0000-0000-0000-000000000001', 'charge',     469.80,  'completed',  'ch_stripe_001', 2.1,  true),
    ('b2000000-0000-0000-0000-000000000002', 'charge',    1188.00,  'completed',  'ch_stripe_002', 1.5,  true),
    ('b2000000-0000-0000-0000-000000000003', 'charge',     690.30,  'completed',  'ch_openpay_003',3.8,  true),
    ('b2000000-0000-0000-0000-000000000004', 'charge',    1236.00,  'completed',  'ch_stripe_004', 1.2,  true),
    ('b2000000-0000-0000-0000-000000000005', 'charge',     577.50,  'completed',  'ch_mp_005',     4.5,  true),
    ('b2000000-0000-0000-0000-000000000007', 'charge',     907.20,  'completed',  'ch_stripe_007', 1.8,  true),
    ('b2000000-0000-0000-0000-000000000008', 'charge',    4590.00,  'completed',  'ch_stripe_008', 0.9,  true),
    -- R09: cargo + reembolso parcial
    ('b2000000-0000-0000-0000-000000000009', 'charge',     566.40,  'completed',  'ch_stripe_009', 2.3,  true),
    ('b2000000-0000-0000-0000-000000000009', 'refund',     283.20,  'completed',  're_stripe_009', NULL, NULL),
    -- R10: cargo completado
    ('b2000000-0000-0000-0000-000000000010', 'charge',     401.70,  'completed',  'ch_stripe_010', 1.1,  true);

-- ============================================
-- 11. NOTIFICATIONS
-- ============================================

INSERT INTO notifications (user_id, type, title, body, related_entity, entity_id, sent_at, read_at, status) VALUES
    -- Juan - confirmación R01
    ('d1000000-0000-0000-0000-000000000001', 'email', '¡Tu reserva está confirmada!',
     'Tu reserva TH-2026-00001 en Hotel Andino Bogotá ha sido confirmada. Check-in: ' || (CURRENT_DATE + 10)::TEXT || '. Código QR adjunto.',
     'reservation', 'a2000000-0000-0000-0000-000000000001',
     NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days', 'sent'),

    ('d1000000-0000-0000-0000-000000000001', 'push', 'Reserva confirmada 🏨',
     'Tu estadía en Hotel Andino Bogotá está lista. ¡Nos vemos pronto!',
     'reservation', 'a2000000-0000-0000-0000-000000000001',
     NOW() - INTERVAL '2 days', NOW() - INTERVAL '1 day', 'sent'),

    -- Sofía - confirmación R02
    ('d1000000-0000-0000-0000-000000000002', 'email', '¡Tu reserva está confirmada!',
     'Tu reserva TH-2026-00002 en Casa Sol Lima ha sido confirmada. Check-in: ' || (CURRENT_DATE + 15)::TEXT || '.',
     'reservation', 'a2000000-0000-0000-0000-000000000002',
     NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days', 'sent'),

    -- Diego - confirmación R03
    ('d1000000-0000-0000-0000-000000000003', 'email', '¡Tu reserva está confirmada!',
     'Tu reserva TH-2026-00003 en Gran Hotel Ciudad de México ha sido confirmada. Check-in: ' || (CURRENT_DATE + 5)::TEXT || '.',
     'reservation', 'a2000000-0000-0000-0000-000000000003',
     NOW() - INTERVAL '1 day', NULL, 'sent'),

    -- Valentina - confirmación R04
    ('d1000000-0000-0000-0000-000000000004', 'email', '¡Tu reserva está confirmada!',
     'Tu reserva TH-2026-00004 en Noi Vitacura Santiago ha sido confirmada. Check-in: ' || (CURRENT_DATE + 20)::TEXT || '.',
     'reservation', 'a2000000-0000-0000-0000-000000000004',
     NOW() - INTERVAL '5 days', NOW() - INTERVAL '4 days', 'sent'),

    -- Martín - confirmación R05
    ('d1000000-0000-0000-0000-000000000005', 'email', '¡Tu reserva está confirmada!',
     'Tu reserva TH-2026-00005 en Palermo Soho Suites ha sido confirmada. Recuerda que la política es no reembolsable.',
     'reservation', 'a2000000-0000-0000-0000-000000000005',
     NOW() - INTERVAL '1 day', NULL, 'sent'),

    -- Camila - reserva pendiente R06
    ('d1000000-0000-0000-0000-000000000006', 'email', 'Reserva en proceso',
     'Tu reserva TH-2026-00006 en Plaza Grande Quito está siendo procesada. Te notificaremos cuando el pago sea confirmado.',
     'reservation', 'a2000000-0000-0000-0000-000000000006',
     NOW() - INTERVAL '4 hours', NOW() - INTERVAL '3 hours', 'sent'),

    -- Juan - cancelación R09
    ('d1000000-0000-0000-0000-000000000001', 'email', 'Reserva cancelada - Reembolso parcial en camino',
     'Tu reserva TH-2026-00009 ha sido cancelada. Según la política de cancelación, recibirás un reembolso de $283.20 USD en 5-7 días hábiles.',
     'reservation', 'a2000000-0000-0000-0000-000000000009',
     NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days', 'sent'),

    -- Sofía - completada R10
    ('d1000000-0000-0000-0000-000000000002', 'email', '¡Gracias por hospedarte con nosotros!',
     'Esperamos que tu estadía en Plaza Grande Quito haya sido memorable. ¡Nos encantaría conocer tu opinión!',
     'reservation', 'a2000000-0000-0000-0000-000000000010',
     NOW() - INTERVAL '7 days', NOW() - INTERVAL '6 days', 'sent'),

    -- Andrés - recordatorio check-in próximo R07
    ('d1000000-0000-0000-0000-000000000007', 'push', 'Check-in en 3 días',
     'Tu check-in en Hotel Andino Bogotá se acerca. Suite Ejecutiva lista para recibirte.',
     'reservation', 'a2000000-0000-0000-0000-000000000007',
     NOW() - INTERVAL '1 hour', NULL, 'sent'),

    -- Isabella - confirmación R08
    ('d1000000-0000-0000-0000-000000000008', 'email', '¡Reserva premium confirmada!',
     'Tu reserva TH-2026-00008 en Penthouse Suite - Casa Sol Lima está confirmada. Nuestro equipo de concierge se pondrá en contacto para coordinar tu experiencia.',
     'reservation', 'a2000000-0000-0000-0000-000000000008',
     NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day', 'sent');

-- ============================================
-- 12. HOTEL REVIEWS (solo para reservas completadas)
-- ============================================

INSERT INTO hotel_reviews (hotel_id, user_id, reservation_id, overall_rating, cleanliness_rating, service_rating, location_rating, value_rating, comment) VALUES
    (
        'b1000000-0000-0000-0000-000000000003',
        'd1000000-0000-0000-0000-000000000002',
        'a2000000-0000-0000-0000-000000000010',
        5.0, 5.0, 4.5, 5.0, 4.5,
        'Una experiencia increíble en el corazón del Centro Histórico de Quito. La habitación colonial era exactamente como las fotos, el servicio impecable y las vistas desde la terraza al atardecer, inolvidables. Definitivamente regresaremos.'
    );

-- ============================================
-- 13. AUDIT LOGS (acciones clave)
-- ============================================

INSERT INTO audit_logs (user_id, action, entity_type, entity_id, ip_address, details) VALUES
    ('d1000000-0000-0000-0000-000000000001', 'reservation_created',  'reservation', 'a2000000-0000-0000-0000-000000000001', '190.24.10.1',  '{"cart_id": "f1000000-0000-0000-0000-000000000001", "room": "Habitación Deluxe"}'),
    ('d1000000-0000-0000-0000-000000000001', 'payment_completed',    'payment',     'b2000000-0000-0000-0000-000000000001', '190.24.10.1',  '{"amount": 469.80, "provider": "Stripe"}'),
    ('d1000000-0000-0000-0000-000000000002', 'reservation_created',  'reservation', 'a2000000-0000-0000-0000-000000000002', '186.33.45.2',  '{"cart_id": "f1000000-0000-0000-0000-000000000002", "room": "Ocean Room"}'),
    ('d1000000-0000-0000-0000-000000000002', 'payment_completed',    'payment',     'b2000000-0000-0000-0000-000000000002', '186.33.45.2',  '{"amount": 1188.00, "provider": "Stripe"}'),
    ('d1000000-0000-0000-0000-000000000001', 'reservation_cancelled','reservation', 'a2000000-0000-0000-0000-000000000009', '190.24.10.1',  '{"reason": "Cambio de planes del viajero", "refund": 283.20}'),
    ('d1000000-0000-0000-0000-000000000003', 'reservation_created',  'reservation', 'a2000000-0000-0000-0000-000000000003', '200.68.12.5',  '{"cart_id": "f1000000-0000-0000-0000-000000000003", "room": "Superior Zócalo"}'),
    ('d1000000-0000-0000-0000-000000000008', 'reservation_created',  'reservation', 'a2000000-0000-0000-0000-000000000008', '186.33.45.3',  '{"cart_id": "f1000000-0000-0000-0000-000000000008", "room": "Penthouse Suite", "amount": 4590.00}');

-- ============================================
-- FIN DEL SEED DE RESERVAS
-- ============================================