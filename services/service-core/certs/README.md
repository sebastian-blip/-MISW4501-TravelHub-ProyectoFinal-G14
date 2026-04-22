# Certificados SSL/TLS para Kafka

Coloca aquí los certificados necesarios para la conexión con Kafka en AWS.

## Archivos esperados

- `ca-cert.pem` - Certificado CA de la autoridad certificadora de Kafka (AWS MSK)

## Configuración

El servicio busca el certificado en:
- Por defecto: `/app/certs/ca-cert.pem` (dentro del contenedor)
- Variable de entorno: `KAFKA_CA_PATH` (puedes sobrescribir la ruta)

## Uso en Docker

### Opción 1: Volumen (recomendado)

```bash
docker run -v /ruta/local/a/certs:/app/certs service-core
```

### Opción 2: Copiar al build

Copia el certificado a esta carpeta antes de construir la imagen:

```bash
cp /ruta/a/ca-cert.pem services/service-core/certs/
docker build -t service-core services/service-core/
```

### Opción 3: Montar desde /service

Si tu infraestructura monta certificados en `/service`:

```bash
docker run -v /service:/service service-core
```

El Dockerfile copiará automáticamente los certificados de `/service` a `/app/certs`.
