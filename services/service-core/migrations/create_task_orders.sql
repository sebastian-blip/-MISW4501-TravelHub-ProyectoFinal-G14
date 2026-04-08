-- SQL para crear la tabla de tareas con estados nombrados (validate, create, cancelation)

-- Eliminar tabla si existe
DROP TABLE IF EXISTS task_orders;

CREATE TABLE task_orders (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'validate',  -- validate, create, cancelation
    history TEXT DEFAULT '["validate"]',              -- JSON array de estados
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Crear índices
CREATE INDEX idx_task_orders_title ON task_orders(title);
CREATE INDEX idx_task_orders_status ON task_orders(status);
