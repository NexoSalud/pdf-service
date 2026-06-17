# NexoSalud PDF Service

Microservicio independiente para generación de PDFs, usando **Python + FastAPI + Playwright + Jinja2**.

Mismo approach que el proyecto original [`gestionContractos`](https://github.com/MaBanguero/gestionContractos).

## Stack

| Componente | Tecnología |
|---|---|
| Framework | FastAPI (Python 3.12) |
| PDF Engine | Playwright (Chromium headless) |
| Templates | Jinja2 |
| Servidor | Uvicorn |

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/pdf/supervision` | Genera PDF de supervisión |
| `POST` | `/api/v1/pdf/resumen` | Genera PDF resumen financiero |

## Request (POST /api/v1/pdf/supervision)

```json
{
  "numero_contrato": "CON-001",
  "contratista": "JUAN PEREZ",
  "identificacion": "1234567890",
  "expedida_en": "CALI",
  "telefono": "5551234",
  "direccion": "CALLE 1 #2-3",
  "tipo_persona": "NATURAL",
  "supervisor": "DRA. MARIA GARCIA",
  "perfil": "MEDICINA",
  "valor_total": 10000000,
  "valor_final": 9500000,
  "tipo_informe": "PARCIAL",
  "periodo_desde": "01/01/2026",
  "periodo_hasta": "31/01/2026",
  "numero_pago": 1,
  "valor_a_pagar": 1500000,
  "otro_si": 0,
  "eps_nombre": "EPS SALUD",
  "eps_valor": 200000,
  "arl_nombre": "ARL SEGURA",
  "arl_valor": 50000,
  "ccf_nombre": "CCF BIENESTAR",
  "ccf_valor": 30000,
  "afp_nombre": "AFP FUTURO",
  "afp_valor": 100000,
  "cuentas_cobro": "CC-001",
  "folios": "5",
  "actividades": "Atencion medica integral\nSeguimiento a tratamientos",
  "observaciones": "Cumplimiento del 95% de metas mensuales."
}
```

## Response
- Si OK → `Content-Type: application/pdf`, attachment `supervision_CON-001.pdf`
- Si falla → `Content-Type: text/html`, attachment `supervision_CON-001.html`
  (el HTML se puede abrir en navegador e imprimir como PDF manualmente)

## Deploy con Docker

```bash
docker build -t pdf-service .
docker run -d -p 8090:8090 pdf-service
```

## Deploy en Coolify
1. Crear nuevo servicio Docker
2. Puerto: `8090`
3. Healthcheck: `/health`
4. Build pack: Dockerfile

## Diseño del PDF
El template HTML está en `templates/supervision.html` y replica exactamente el diseño del proyecto original:
- Formato único de supervisión con tabla de 4 columnas
- Header azul (#a2c8ec) "FORMATO UNICO INFORME DE SUPERVISION"
- Datos del contratista, supervisor, identificación
- Seguridad social (IBC, EPS, ARL, AFP, SENA, ICBF, CCF)
- Actividades con checkboxes (X)
- Observaciones, anexos y folios
- Firmas del supervisor y contratista
