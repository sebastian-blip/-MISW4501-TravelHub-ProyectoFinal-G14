-- ============================================
-- SEED DATA: TravelHub - Hoteles y Habitaciones
-- ============================================
-- Prerequisito: countries ya insertados (seed del schema)
-- UUIDs fijos para mantener coherencia entre tablas

-- ============================================
-- 1. USERS (dueños de los hoteles)
-- ============================================

INSERT INTO users (id, email, password_hash, first_name, last_name, phone, user_type, email_verified, active) VALUES
    ('a1000000-0000-0000-0000-000000000001', 'admin.bogota@travelhub.com',   '$2b$12$placeholderHashBogota',   'Carlos',    'Rodríguez', '+573001234567', 'hotel_admin', true, true),
    ('a1000000-0000-0000-0000-000000000002', 'admin.lima@travelhub.com',     '$2b$12$placeholderHashLima',     'María',     'Quispe',    '+51987654321',  'hotel_admin', true, true),
    ('a1000000-0000-0000-0000-000000000003', 'admin.quito@travelhub.com',    '$2b$12$placeholderHashQuito',    'Andrés',    'Morales',   '+59398765432',  'hotel_admin', true, true),
    ('a1000000-0000-0000-0000-000000000004', 'admin.cdmx@travelhub.com',     '$2b$12$placeholderHashCDMX',     'Lucía',     'Hernández', '+5215512345678','hotel_admin', true, true),
    ('a1000000-0000-0000-0000-000000000005', 'admin.santiago@travelhub.com', '$2b$12$placeholderHashSantiago', 'Rodrigo',   'Fuentes',   '+56912345678',  'hotel_admin', true, true),
    ('a1000000-0000-0000-0000-000000000006', 'admin.baires@travelhub.com',   '$2b$12$placeholderHashBaires',   'Valentina', 'Gutiérrez', '+5491112345678','hotel_admin', true, true);

-- ============================================
-- 2. HOTELS (uno por país)
-- ============================================

INSERT INTO hotels (id, name, description, address, city, country_id, latitude, longitude, phone, email, stars, rating, total_reviews, check_in_time, check_out_time, owner_user_id, pms_provider, pms_hotel_code, active) VALUES

    -- Colombia
    (
        'b1000000-0000-0000-0000-000000000001',
        'Hotel Andino Bogotá',
        'Hotel boutique ubicado en el corazón de la Zona Rosa de Bogotá. Combina el estilo colonial con comodidades modernas, a pasos de los mejores restaurantes y centros comerciales de la ciudad.',
        'Calle 82 #11-37, Zona Rosa',
        'Bogotá',
        (SELECT id FROM countries WHERE code = 'COL'),
        4.66590, -74.05290,
        '+573012345678', 'reservas@hotelAndino.com.co',
        4, 4.5, 312,
        '15:00:00', '12:00:00',
        'a1000000-0000-0000-0000-000000000001',
        'RoomRaccoon', 'HTL-COL-001',
        true
    ),

    -- Perú
    (
        'b1000000-0000-0000-0000-000000000002',
        'Casa Sol Lima',
        'Hotel de lujo frente al Océano Pacífico en el distrito de Miraflores. Disfrute de vistas panorámicas al mar, gastronomía de primer nivel y acceso directo al Parque del Amor.',
        'Malecón de la Reserva 1035, Miraflores',
        'Lima',
        (SELECT id FROM countries WHERE code = 'PER'),
        -12.13282, -77.02839,
        '+51016543210', 'reservas@casasollima.pe',
        5, 4.8, 578,
        '14:00:00', '12:00:00',
        'a1000000-0000-0000-0000-000000000002',
        'TravelClick', 'HTL-PER-001',
        true
    ),

    -- Ecuador
    (
        'b1000000-0000-0000-0000-000000000003',
        'Plaza Grande Quito',
        'Histórico hotel frente a la Plaza de la Independencia, en el Centro Histórico de Quito, Patrimonio de la Humanidad. Arquitectura colonial restaurada con todas las comodidades contemporáneas.',
        'García Moreno N5-16 y Chile, Centro Histórico',
        'Quito',
        (SELECT id FROM countries WHERE code = 'ECU'),
        -0.22016, -78.51234,
        '+593022876543', 'info@plazagrandequito.ec',
        5, 4.7, 421,
        '15:00:00', '11:00:00',
        'a1000000-0000-0000-0000-000000000003',
        'Hotelbeds', 'HTL-ECU-001',
        true
    ),

    -- México
    (
        'b1000000-0000-0000-0000-000000000004',
        'Gran Hotel Ciudad de México',
        'Ícono arquitectónico del Porfiriato ubicado frente al Zócalo capitalino. Su impresionante vitral Tiffany de 1908 y sus jaulas de ascensores originales lo convierten en un destino único.',
        '16 de Septiembre 82, Centro Histórico',
        'Ciudad de México',
        (SELECT id FROM countries WHERE code = 'MEX'),
        19.43262, -99.13318,
        '+525555109182', 'reservaciones@granhotelcdmx.com.mx',
        4, 4.3, 894,
        '15:00:00', '12:00:00',
        'a1000000-0000-0000-0000-000000000004',
        'RoomRaccoon', 'HTL-MEX-001',
        true
    ),

    -- Chile
    (
        'b1000000-0000-0000-0000-000000000005',
        'Noi Vitacura Santiago',
        'Hotel de diseño contemporáneo en el exclusivo barrio de Vitacura. Minimalismo chileno con arte local, piscina exterior climatizada y restaurante de autor con ingredientes de temporada.',
        'Nueva Costanera 3736, Vitacura',
        'Santiago',
        (SELECT id FROM countries WHERE code = 'CHL'),
        -33.40128, -70.57921,
        '+56227953900', 'reservas@noivitacura.cl',
        4, 4.6, 267,
        '15:00:00', '12:00:00',
        'a1000000-0000-0000-0000-000000000005',
        'TravelClick', 'HTL-CHL-001',
        true
    ),

    -- Argentina
    (
        'b1000000-0000-0000-0000-000000000006',
        'Palermo Soho Suites',
        'Boutique hotel en el barrio más bohemio de Buenos Aires. Rodeado de galerías de arte, cafeterías de especialidad y la mejor propuesta gastronómica de la ciudad.',
        'El Salvador 4916, Palermo Soho',
        'Buenos Aires',
        (SELECT id FROM countries WHERE code = 'ARG'),
        -34.58742, -58.43198,
        '+541148312000', 'hello@palermosohosuites.com.ar',
        4, 4.4, 389,
        '14:00:00', '11:00:00',
        'a1000000-0000-0000-0000-000000000006',
        'Hotelbeds', 'HTL-ARG-001',
        true
    );

-- ============================================
-- 3. HOTEL AMENITIES
-- ============================================

INSERT INTO hotel_amenities (hotel_id, name, icon) VALUES
    -- Hotel Andino Bogotá
    ('b1000000-0000-0000-0000-000000000001', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000001', 'parking',           'local_parking'),
    ('b1000000-0000-0000-0000-000000000001', 'restaurant',        'restaurant'),
    ('b1000000-0000-0000-0000-000000000001', 'gym',               'fitness_center'),
    ('b1000000-0000-0000-0000-000000000001', 'business_center',   'business_center'),
    ('b1000000-0000-0000-0000-000000000001', 'room_service',      'room_service'),

    -- Casa Sol Lima
    ('b1000000-0000-0000-0000-000000000002', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000002', 'pool',              'pool'),
    ('b1000000-0000-0000-0000-000000000002', 'spa',               'spa'),
    ('b1000000-0000-0000-0000-000000000002', 'restaurant',        'restaurant'),
    ('b1000000-0000-0000-0000-000000000002', 'gym',               'fitness_center'),
    ('b1000000-0000-0000-0000-000000000002', 'valet_parking',     'local_parking'),
    ('b1000000-0000-0000-0000-000000000002', 'concierge',         'concierge'),

    -- Plaza Grande Quito
    ('b1000000-0000-0000-0000-000000000003', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000003', 'restaurant',        'restaurant'),
    ('b1000000-0000-0000-0000-000000000003', 'bar',               'local_bar'),
    ('b1000000-0000-0000-0000-000000000003', 'room_service',      'room_service'),
    ('b1000000-0000-0000-0000-000000000003', 'concierge',         'concierge'),
    ('b1000000-0000-0000-0000-000000000003', 'laundry',           'local_laundry_service'),

    -- Gran Hotel CDMX
    ('b1000000-0000-0000-0000-000000000004', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000004', 'restaurant',        'restaurant'),
    ('b1000000-0000-0000-0000-000000000004', 'bar',               'local_bar'),
    ('b1000000-0000-0000-0000-000000000004', 'room_service',      'room_service'),
    ('b1000000-0000-0000-0000-000000000004', 'business_center',   'business_center'),
    ('b1000000-0000-0000-0000-000000000004', 'parking',           'local_parking'),

    -- Noi Vitacura Santiago
    ('b1000000-0000-0000-0000-000000000005', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000005', 'pool',              'pool'),
    ('b1000000-0000-0000-0000-000000000005', 'gym',               'fitness_center'),
    ('b1000000-0000-0000-0000-000000000005', 'restaurant',        'restaurant'),
    ('b1000000-0000-0000-0000-000000000005', 'parking',           'local_parking'),
    ('b1000000-0000-0000-0000-000000000005', 'pet_friendly',      'pets'),

    -- Palermo Soho Suites
    ('b1000000-0000-0000-0000-000000000006', 'wifi',              'wifi'),
    ('b1000000-0000-0000-0000-000000000006', 'breakfast_included','free_breakfast'),
    ('b1000000-0000-0000-0000-000000000006', 'bar',               'local_bar'),
    ('b1000000-0000-0000-0000-000000000006', 'room_service',      'room_service'),
    ('b1000000-0000-0000-0000-000000000006', 'terrace',           'deck');

-- ============================================
-- 4. HOTEL IMAGES (placeholders Unsplash)
-- ============================================

INSERT INTO hotel_images (hotel_id, url, alt_text, sort_order, image_type) VALUES
    -- Hotel Andino Bogotá
    ('b1000000-0000-0000-0000-000000000001', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1200', 'Fachada Hotel Andino Bogotá',       0, 'main'),
    ('b1000000-0000-0000-0000-000000000001', 'https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=1200', 'Lobby Hotel Andino',                 1, 'gallery'),
    ('b1000000-0000-0000-0000-000000000001', 'https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=1200', 'Restaurante Hotel Andino',           2, 'gallery'),

    -- Casa Sol Lima
    ('b1000000-0000-0000-0000-000000000002', 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=1200', 'Vista al Pacífico - Casa Sol Lima',  0, 'main'),
    ('b1000000-0000-0000-0000-000000000002', 'https://images.unsplash.com/photo-1551882547-ff40c4a49f4e?w=1200', 'Piscina infinita Casa Sol',           1, 'gallery'),
    ('b1000000-0000-0000-0000-000000000002', 'https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1200', 'Suite Premium Casa Sol',             2, 'gallery'),

    -- Plaza Grande Quito
    ('b1000000-0000-0000-0000-000000000003', 'https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=1200', 'Fachada colonial Plaza Grande',      0, 'main'),
    ('b1000000-0000-0000-0000-000000000003', 'https://images.unsplash.com/photo-1444201983204-c43cbd584d93?w=1200', 'Vista al Centro Histórico Quito',    1, 'gallery'),

    -- Gran Hotel CDMX
    ('b1000000-0000-0000-0000-000000000004', 'https://images.unsplash.com/photo-1496417263034-38ec4f0b665a?w=1200', 'Vitral Tiffany Gran Hotel CDMX',    0, 'main'),
    ('b1000000-0000-0000-0000-000000000004', 'https://images.unsplash.com/photo-1590490360182-c33d57733427?w=1200', 'Habitación Gran Hotel CDMX',         1, 'gallery'),

    -- Noi Vitacura
    ('b1000000-0000-0000-0000-000000000005', 'https://images.unsplash.com/photo-1629140727571-9b5c6f6267b4?w=1200', 'Exterior Noi Vitacura',              0, 'main'),
    ('b1000000-0000-0000-0000-000000000005', 'https://images.unsplash.com/photo-1575429198097-0414ec08e8cd?w=1200', 'Piscina exterior Noi Vitacura',      1, 'gallery'),

    -- Palermo Soho Suites
    ('b1000000-0000-0000-0000-000000000006', 'https://images.unsplash.com/photo-1522798514-97ceb8c4f1c8?w=1200', 'Terraza Palermo Soho Suites',         0, 'main'),
    ('b1000000-0000-0000-0000-000000000006', 'https://images.unsplash.com/photo-1455587734955-081b22074882?w=1200', 'Suite Palermo Soho',                  1, 'gallery');

-- ============================================
-- 5. ROOM TYPES (3 por hotel: Standard, Deluxe, Suite)
-- ============================================

INSERT INTO room_types (id, hotel_id, name, description, base_price, max_capacity, bed_type, size_sqm, total_units, active) VALUES

    -- Hotel Andino Bogotá (precios en COP equivalente USD)
    ('c1000000-0000-0000-0000-000000000101', 'b1000000-0000-0000-0000-000000000001', 'Habitación Estándar',
     'Habitación acogedora con cama doble o twin, baño privado, minibar y vista al jardín interior.',
     85.00, 2, 'queen', 22.0, 15, true),
    ('c1000000-0000-0000-0000-000000000102', 'b1000000-0000-0000-0000-000000000001', 'Habitación Deluxe',
     'Habitación superior con cama king size, bañera de hidromasaje, balcón privado y vista a la Zona Rosa.',
     145.00, 3, 'king', 32.0, 10, true),
    ('c1000000-0000-0000-0000-000000000103', 'b1000000-0000-0000-0000-000000000001', 'Suite Ejecutiva',
     'Suite de dos ambientes con sala de estar, comedor, kitchenette equipada, jacuzzi y terraza panorámica.',
     280.00, 4, 'king', 60.0, 4, true),

    -- Casa Sol Lima
    ('c1000000-0000-0000-0000-000000000201', 'b1000000-0000-0000-0000-000000000002', 'Ocean Room',
     'Habitación con vista directa al Océano Pacífico, cama king, ducha lluvia y deck privado.',
     220.00, 2, 'king', 35.0, 20, true),
    ('c1000000-0000-0000-0000-000000000202', 'b1000000-0000-0000-0000-000000000002', 'Deluxe Ocean View',
     'Habitación amplia con vista panorámica al mar, bañera independiente, sala de estar y servicio de mayordomo.',
     380.00, 3, 'king', 55.0, 10, true),
    ('c1000000-0000-0000-0000-000000000203', 'b1000000-0000-0000-0000-000000000002', 'Penthouse Suite',
     'Suite exclusiva en planta alta con terraza privada frente al mar, piscina personal y acceso VIP al spa.',
     850.00, 4, 'king', 120.0, 2, true),

    -- Plaza Grande Quito
    ('c1000000-0000-0000-0000-000000000301', 'b1000000-0000-0000-0000-000000000003', 'Habitación Colonial',
     'Habitación con decoración colonial restaurada, vista a la Plaza de la Independencia y mobiliario de época.',
     130.00, 2, 'queen', 28.0, 12, true),
    ('c1000000-0000-0000-0000-000000000302', 'b1000000-0000-0000-0000-000000000003', 'Habitación Presidencial',
     'Habitación premium con vista a la iglesia de La Compañía, baño en mármol y amenidades de lujo.',
     210.00, 2, 'king', 40.0, 6, true),
    ('c1000000-0000-0000-0000-000000000303', 'b1000000-0000-0000-0000-000000000003', 'Suite Gran Plaza',
     'Suite con terraza frente al Centro Histórico, sala independiente, comedor y servicio de mayordomo 24h.',
     420.00, 4, 'king', 85.0, 3, true),

    -- Gran Hotel CDMX
    ('c1000000-0000-0000-0000-000000000401', 'b1000000-0000-0000-0000-000000000004', 'Habitación Clásica',
     'Habitación de estilo porfiriano con vista al Zócalo, cama matrimonial, escritorio y baño de mármol.',
     110.00, 2, 'double', 25.0, 25, true),
    ('c1000000-0000-0000-0000-000000000402', 'b1000000-0000-0000-0000-000000000004', 'Habitación Superior Zócalo',
     'Habitación superior con vista privilegiada al Zócalo y la Catedral Metropolitana, cama king y sala de estar.',
     195.00, 3, 'king', 38.0, 12, true),
    ('c1000000-0000-0000-0000-000000000403', 'b1000000-0000-0000-0000-000000000004', 'Suite Histórica',
     'La suite más emblemática del hotel, con vista de 180° al Zócalo, sala de juntas privada y decoración original.',
     450.00, 4, 'king', 90.0, 3, true),

    -- Noi Vitacura Santiago
    ('c1000000-0000-0000-0000-000000000501', 'b1000000-0000-0000-0000-000000000005', 'Habitación Design',
     'Habitación minimalista con arte chileno original, cama king, ducha doble y acceso al jardín exterior.',
     160.00, 2, 'king', 30.0, 18, true),
    ('c1000000-0000-0000-0000-000000000502', 'b1000000-0000-0000-0000-000000000005', 'Habitación Pool View',
     'Habitación con vista a la piscina exterior, terraza privada, bañera independiente y minibar premium.',
     240.00, 2, 'king', 45.0, 8, true),
    ('c1000000-0000-0000-0000-000000000503', 'b1000000-0000-0000-0000-000000000005', 'Suite Noi',
     'Suite de autor con sala de estar, comedor privado, terraza con piscina plunge y servicio de chef a pedido.',
     520.00, 4, 'king', 100.0, 3, true),

    -- Palermo Soho Suites
    ('c1000000-0000-0000-0000-000000000601', 'b1000000-0000-0000-0000-000000000006', 'Estudio Soho',
     'Estudio moderno con kitchenette equipada, espacio de trabajo, cama queen y desayuno incluido.',
     95.00, 2, 'queen', 28.0, 14, true),
    ('c1000000-0000-0000-0000-000000000602', 'b1000000-0000-0000-0000-000000000006', 'Suite Palermo',
     'Suite con sala de estar independiente, terraza privada con vista al barrio, cocina completa y bañera.',
     175.00, 3, 'king', 50.0, 7, true),
    ('c1000000-0000-0000-0000-000000000603', 'b1000000-0000-0000-0000-000000000006', 'Suite Ático',
     'Ático exclusivo con terraza de 80m² sobre los techos de Palermo, piscina privada y cocina gourmet equipada.',
     380.00, 4, 'king', 130.0, 2, true);

-- ============================================
-- 6. ROOM AMENITIES
-- ============================================

INSERT INTO room_amenities (room_type_id, name, icon) VALUES
    -- Estándar Bogotá
    ('c1000000-0000-0000-0000-000000000101', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000101', 'ac',        'ac_unit'),
    ('c1000000-0000-0000-0000-000000000101', 'minibar',   'local_bar'),
    ('c1000000-0000-0000-0000-000000000101', 'safe',      'lock'),
    -- Deluxe Bogotá
    ('c1000000-0000-0000-0000-000000000102', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000102', 'ac',        'ac_unit'),
    ('c1000000-0000-0000-0000-000000000102', 'minibar',   'local_bar'),
    ('c1000000-0000-0000-0000-000000000102', 'jacuzzi',   'hot_tub'),
    ('c1000000-0000-0000-0000-000000000102', 'balcony',   'balcony'),
    ('c1000000-0000-0000-0000-000000000102', 'safe',      'lock'),
    -- Suite Bogotá
    ('c1000000-0000-0000-0000-000000000103', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000103', 'ac',        'ac_unit'),
    ('c1000000-0000-0000-0000-000000000103', 'minibar',   'local_bar'),
    ('c1000000-0000-0000-0000-000000000103', 'jacuzzi',   'hot_tub'),
    ('c1000000-0000-0000-0000-000000000103', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000103', 'terrace',   'deck'),
    ('c1000000-0000-0000-0000-000000000103', 'safe',      'lock'),

    -- Ocean Room Lima
    ('c1000000-0000-0000-0000-000000000201', 'ocean_view','waves'),
    ('c1000000-0000-0000-0000-000000000201', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000201', 'minibar',   'local_bar'),
    ('c1000000-0000-0000-0000-000000000201', 'rain_shower','shower'),
    -- Deluxe Lima
    ('c1000000-0000-0000-0000-000000000202', 'ocean_view','waves'),
    ('c1000000-0000-0000-0000-000000000202', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000202', 'minibar',   'local_bar'),
    ('c1000000-0000-0000-0000-000000000202', 'bathtub',   'bathtub'),
    ('c1000000-0000-0000-0000-000000000202', 'balcony',   'balcony'),
    -- Penthouse Lima
    ('c1000000-0000-0000-0000-000000000203', 'ocean_view','waves'),
    ('c1000000-0000-0000-0000-000000000203', 'private_pool','pool'),
    ('c1000000-0000-0000-0000-000000000203', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000203', 'terrace',   'deck'),
    ('c1000000-0000-0000-0000-000000000203', 'butler',    'concierge'),

    -- Colonial Quito
    ('c1000000-0000-0000-0000-000000000301', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000301', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000301', 'safe',      'lock'),
    -- Presidencial Quito
    ('c1000000-0000-0000-0000-000000000302', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000302', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000302', 'bathtub',   'bathtub'),
    ('c1000000-0000-0000-0000-000000000302', 'safe',      'lock'),
    -- Suite Quito
    ('c1000000-0000-0000-0000-000000000303', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000303', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000303', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000303', 'terrace',   'deck'),
    ('c1000000-0000-0000-0000-000000000303', 'butler',    'concierge'),

    -- Clásica CDMX
    ('c1000000-0000-0000-0000-000000000401', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000401', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000401', 'safe',      'lock'),
    -- Superior CDMX
    ('c1000000-0000-0000-0000-000000000402', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000402', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000402', 'balcony',   'balcony'),
    ('c1000000-0000-0000-0000-000000000402', 'safe',      'lock'),
    -- Suite CDMX
    ('c1000000-0000-0000-0000-000000000403', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000403', 'city_view', 'location_city'),
    ('c1000000-0000-0000-0000-000000000403', 'meeting_room','meeting_room'),
    ('c1000000-0000-0000-0000-000000000403', 'terrace',   'deck'),

    -- Design Santiago
    ('c1000000-0000-0000-0000-000000000501', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000501', 'garden_view','park'),
    ('c1000000-0000-0000-0000-000000000501', 'rain_shower','shower'),
    -- Pool View Santiago
    ('c1000000-0000-0000-0000-000000000502', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000502', 'pool_view', 'pool'),
    ('c1000000-0000-0000-0000-000000000502', 'bathtub',   'bathtub'),
    ('c1000000-0000-0000-0000-000000000502', 'terrace',   'deck'),
    -- Suite Santiago
    ('c1000000-0000-0000-0000-000000000503', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000503', 'private_pool','pool'),
    ('c1000000-0000-0000-0000-000000000503', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000503', 'terrace',   'deck'),

    -- Estudio Buenos Aires
    ('c1000000-0000-0000-0000-000000000601', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000601', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000601', 'workspace', 'desk'),
    -- Suite BA
    ('c1000000-0000-0000-0000-000000000602', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000602', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000602', 'terrace',   'deck'),
    ('c1000000-0000-0000-0000-000000000602', 'bathtub',   'bathtub'),
    -- Ático BA
    ('c1000000-0000-0000-0000-000000000603', 'tv',        'tv'),
    ('c1000000-0000-0000-0000-000000000603', 'private_pool','pool'),
    ('c1000000-0000-0000-0000-000000000603', 'kitchen',   'kitchen'),
    ('c1000000-0000-0000-0000-000000000603', 'rooftop',   'rooftop');

-- ============================================
-- 7. INVENTORY CALENDAR (próximos 60 días)
-- Precios con variación fin de semana y temporada
-- ============================================

INSERT INTO inventory_calendar (room_type_id, date, available_units, price_per_night, currency_code, minimum_stay)
SELECT
    rt.id                                                            AS room_type_id,
    (CURRENT_DATE + s.day)::DATE                                     AS date,
    -- Unidades disponibles: reducidas fin de semana (mayor ocupación)
    CASE
        WHEN EXTRACT(DOW FROM (CURRENT_DATE + s.day)) IN (5, 6) -- viernes/sábado
        THEN GREATEST(1, rt.total_units - FLOOR(rt.total_units * 0.5)::INT)
        ELSE GREATEST(2, rt.total_units - FLOOR(rt.total_units * 0.2)::INT)
    END                                                              AS available_units,
    -- Precio con variación: +20% fin de semana, base el resto
    ROUND(
        rt.base_price * CASE
            WHEN EXTRACT(DOW FROM (CURRENT_DATE + s.day)) IN (5, 6) THEN 1.20
            WHEN EXTRACT(DOW FROM (CURRENT_DATE + s.day)) = 0       THEN 1.10
            ELSE 1.00
        END,
    2)                                                               AS price_per_night,
    'USD'                                                            AS currency_code,
    1                                                                AS minimum_stay
FROM room_types rt
CROSS JOIN generate_series(1, 60) AS s(day)
WHERE rt.active = true;

-- ============================================
-- 8. RATE PLANS
-- ============================================

INSERT INTO rate_plans (hotel_id, name, discount_pct, valid_from, valid_to, minimum_stay, refundable, active) VALUES
    -- Bogotá
    ('b1000000-0000-0000-0000-000000000001', 'Early Bird 15%',         15.00, CURRENT_DATE, CURRENT_DATE + 90,  3, true,  true),
    ('b1000000-0000-0000-0000-000000000001', 'No Reembolsable 20%',    20.00, CURRENT_DATE, CURRENT_DATE + 180, 1, false, true),
    -- Lima
    ('b1000000-0000-0000-0000-000000000002', 'Paquete Romántico 10%',  10.00, CURRENT_DATE, CURRENT_DATE + 90,  2, true,  true),
    ('b1000000-0000-0000-0000-000000000002', 'Tarifa No Flex 25%',     25.00, CURRENT_DATE, CURRENT_DATE + 180, 2, false, true),
    -- Quito
    ('b1000000-0000-0000-0000-000000000003', 'Semana Completa 15%',    15.00, CURRENT_DATE, CURRENT_DATE + 120, 7, true,  true),
    ('b1000000-0000-0000-0000-000000000003', 'No Reembolsable 18%',    18.00, CURRENT_DATE, CURRENT_DATE + 180, 1, false, true),
    -- CDMX
    ('b1000000-0000-0000-0000-000000000004', 'Corporativo 12%',        12.00, CURRENT_DATE, CURRENT_DATE + 365, 1, true,  true),
    ('b1000000-0000-0000-0000-000000000004', 'No Reembolsable 22%',    22.00, CURRENT_DATE, CURRENT_DATE + 180, 1, false, true),
    -- Santiago
    ('b1000000-0000-0000-0000-000000000005', 'Estadía Extendida 15%',  15.00, CURRENT_DATE, CURRENT_DATE + 90,  5, true,  true),
    ('b1000000-0000-0000-0000-000000000005', 'Tarifa No Flex 20%',     20.00, CURRENT_DATE, CURRENT_DATE + 180, 2, false, true),
    -- Buenos Aires
    ('b1000000-0000-0000-0000-000000000006', 'Desayuno Incluido 8%',    8.00, CURRENT_DATE, CURRENT_DATE + 90,  2, true,  true),
    ('b1000000-0000-0000-0000-000000000006', 'No Reembolsable 20%',    20.00, CURRENT_DATE, CURRENT_DATE + 180, 1, false, true);

-- ============================================
-- 9. SPECIAL OFFERS
-- ============================================

INSERT INTO special_offers (hotel_id, room_type_id, title, description, discount_pct, valid_from, valid_to, active) VALUES
    (
        'b1000000-0000-0000-0000-000000000001',
        'c1000000-0000-0000-0000-000000000102',
        'Escapada de Lujo Bogotá',
        '20% de descuento en habitaciones Deluxe reservando con 15 días de anticipación.',
        20.00, CURRENT_DATE, CURRENT_DATE + 45, true
    ),
    (
        'b1000000-0000-0000-0000-000000000002',
        NULL,
        'Verano en el Pacífico',
        'Hasta 25% de descuento en todas las habitaciones durante los meses de verano.',
        25.00, CURRENT_DATE, CURRENT_DATE + 60, true
    ),
    (
        'b1000000-0000-0000-0000-000000000003',
        'c1000000-0000-0000-0000-000000000301',
        'Cultura y Herencia Quito',
        '15% off en habitaciones coloniales para viajeros interesados en tours culturales.',
        15.00, CURRENT_DATE, CURRENT_DATE + 30, true
    ),
    (
        'b1000000-0000-0000-0000-000000000004',
        'c1000000-0000-0000-0000-000000000401',
        'Midweek City Escape',
        '18% de descuento de lunes a jueves en habitaciones clásicas.',
        18.00, CURRENT_DATE, CURRENT_DATE + 90, true
    ),
    (
        'b1000000-0000-0000-0000-000000000005',
        NULL,
        'Primavera en Vitacura',
        '12% de descuento en todas las categorías durante septiembre y octubre.',
        12.00, CURRENT_DATE, CURRENT_DATE + 60, true
    ),
    (
        'b1000000-0000-0000-0000-000000000006',
        'c1000000-0000-0000-0000-000000000603',
        'Ático Exclusivo Buenos Aires',
        '10% de descuento en el Suite Ático para estadías mínimas de 3 noches.',
        10.00, CURRENT_DATE, CURRENT_DATE + 45, true
    );

-- ============================================
-- FIN DEL SEED
-- ============================================
