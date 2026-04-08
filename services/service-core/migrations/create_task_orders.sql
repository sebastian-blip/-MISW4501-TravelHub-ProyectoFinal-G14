-- SQL para crear la tabla de tareas con pasos numéricos (1-4)

-- Eliminar tabla si existe
DROP TABLE IF EXISTS task_orders;

CREATE TABLE task_orders (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status INTEGER NOT NULL DEFAULT 1,  -- 1=step_one, 2=step_two, 3=step_three, 4=step_four
    history TEXT DEFAULT '[1]',         -- JSON array de pasos: [1, 2, 3]
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Crear índices
CREATE INDEX idx_task_orders_title ON task_orders(title);
CREATE INDEX idx_task_orders_status ON task_orders(status);
