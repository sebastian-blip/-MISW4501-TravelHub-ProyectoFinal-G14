# Guía de desarrollo (Monorepo microservicios + GitOps)

Esta plataforma usa:

- **Monorepo** con microservicios en `services/<service-name>/`
- **Manifiestos Kubernetes** por servicio en `<service-dir>/k8s/` (Kustomize)
- **CI/CD** con GitHub Actions
- **Despliegue continuo (GitOps)** con Argo CD (el cluster se sincroniza automáticamente con lo que está en Git)

**Código compartido (no es un microservicio):** la librería hexagonal (`ports/`, `contracts/`, `adapters/`) vive en `libs/service_external/`.

---

## 1. Estructura del repositorio

### 1.1 Microservicios (build)

Cada microservicio vive en su directorio con **todo lo necesario** para construirlo y desplegarlo:

```
services/<service-name>/
  Dockerfile
  k8s/
    kustomization.yaml   (obligatorio para GitOps)
    deployment.yaml      (recomendado)
    service.yaml         (recomendado)
    ingress.yaml         (si expone HTTP)
  app/
    ...código fuente...
  requirements.txt
```

Los **adapters de integraciones externas** van bajo `services/service-external/<name>/` y comparten la librería hexagonal `libs/service_external/`. Cada uno sigue patrón hexagonal: `app/ports/`, `app/adapters/` (con Strategy pattern), `app/main.py`.

Ejemplos:

- `services/service-core/`
- `services/service-external/payment/`
- `services/service-external/notification/`
- `services/service-external/pms/`
- `services/service-external/maps/`
- `services/service-external/cdn-storage/`
- `services/service-external/currency/`

### 1.2 Kubernetes (deploy / GitOps)

Cada microservicio que se despliega tiene su directorio `k8s/` **dentro del servicio**:

- `<service-dir>/k8s/`
  - **kustomization.yaml** (obligatorio para GitOps)
  - **deployment.yaml** (recomendado)
  - **service.yaml** (recomendado)
  - **ingress.yaml** (si expone HTTP público)

Ejemplos:

- `services/service-external/payment/k8s/`
- `services/service-external/maps/k8s/`
- `services/service-core/k8s/`

### 1.3 Build

**Adapters externos** (copian `libs/service_external`, contexto = raíz del repo):

```bash
docker build -f services/service-external/<name>/Dockerfile -t <tag> .
```

**Servicios estándar** (contexto = carpeta del servicio):

```bash
docker build -t <tag> services/<service-name>
```

---

## 2. Flujo de trabajo recomendado (Trunk-Based Development)

- `main` debe estar siempre en estado desplegable.
- Todo cambio entra por **Pull Request** y ramas cortas.

### 2.1 Pasos típicos

1. Crear una rama desde `main`: `feat/<service>-<descripcion>` o `fix/<service>-<descripcion>`.
2. Realizar cambios en el servicio (código + `k8s/` si aplica) y/o `libs/service_external/`.
3. Abrir PR hacia `main`.
4. CI corre (build / test / lint).
5. Merge a `main`.

---

## 3. Qué pasa al hacer merge a main (CI/CD + GitOps)

1. GitHub Actions detecta servicios con **Dockerfile**.
2. Si cambia `libs/service_external/`, se reconstruyen todos los adapters bajo `services/service-external/`.
3. Por cada servicio afectado, se construye la imagen Docker.
4. En modo real: se publica la imagen en ECR.
5. Se actualiza `<service-dir>/k8s/kustomization.yaml` (bump del tag de imagen = SHA del commit).
6. Ese cambio se commitea al repo.
7. Argo CD detecta el cambio en Git y aplica el despliegue al cluster.

---

## 4. Cómo agregar un microservicio nuevo (plug & play)

1. Crear `services/<name>/` (o `services/service-external/<name>/`) con `Dockerfile` + código.
2. Crear `<service-dir>/k8s/` con `kustomization.yaml`, `deployment.yaml`, `service.yaml`.
3. Listo — la CI lo detecta automáticamente.

---

## 5. Kustomize

`kustomization.yaml` permite que la CI actualice el tag con:

```bash
kustomize edit set image <nombre>:latest=<ecr>/<prefijo>/<svc>:<sha>
```

---

## 6. Estándares por servicio

### Health checks

- `GET /health` (liveness)
- `GET /ready` (readiness)

### Puerto y variables

Documentar puerto (ej. 8080) y variables en el README del servicio.

### Logs

Log a **stdout/stderr** (12-factor).

---

## 7. Convenciones de PRs y commits

- PRs pequeños y enfocados.
- Mensajes tipo: `feat(payment): add refund`, `fix(maps): handle timeout`, `chore(k8s): bump image`.

---

## 8. Desarrollo local

```bash
# Adapter externo (contexto = raíz)
docker build -f services/service-external/payment/Dockerfile -t local/payment:dev .
docker run --rm -p 8080:8080 -e ADAPTER_STRATEGY=mock local/payment:dev

# Servicio estándar (contexto = carpeta)
docker build -t local/service-core:dev services/service-core
docker run --rm -p 8000:8000 local/service-core:dev
```
