"""
NexoSalud PDF Service - Generacion de PDFs con Playwright + Jinja2
Mismo approach que el proyecto original gestionContractos (MaBanguero)
"""
import os
import re
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pdf-service")

app = FastAPI(title="NexoSalud PDF Service", version="1.0.0")
templates = Environment(loader=FileSystemLoader("templates"), autoescape=False)

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

# ============================================================
# MODELOS
# ============================================================

class SupervisionPDFRequest(BaseModel):
    numero_contrato: str = ""
    contratista: str = ""
    identificacion: str = ""
    expedida_en: str = ""
    telefono: str = ""
    direccion: str = ""
    tipo_persona: str = ""
    supervisor: str = ""
    perfil: str = ""
    valor_total: float = 0
    valor_final: Optional[float] = None
    tipo_informe: str = ""
    periodo_desde: str = ""
    periodo_hasta: str = ""
    numero_pago: int = 0
    valor_a_pagar: float = 0
    otro_si: float = 0
    eps_nombre: str = ""
    eps_valor: float = 0
    arl_nombre: str = ""
    arl_valor: float = 0
    ccf_nombre: str = ""
    ccf_valor: float = 0
    afp_nombre: str = ""
    afp_valor: float = 0
    cuentas_cobro: str = ""
    folios: str = ""
    actividades: str = ""
    observaciones: str = ""
    objeto_contrato: str = "-"
    anexos: str = "-"
    fecha_firma: str = ""
    formato: str = "pdf"  # "pdf" o "html"

class HealthResponse(BaseModel):
    status: str = "ok"

# ============================================================
# PRE-WARMUP
# ============================================================

@app.on_event("startup")
async def prewarm():
    """Pre-calienta Playwright descargando browsers al iniciar"""
    log.info("Pre-warming Playwright...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--no-zygote"]
            )
            page = await browser.new_page()
            await page.set_content("<html><body><p>Prewarm</p></body></html>")
            await page.wait_for_load_state("networkidle")
            pdf = await page.pdf(format="Letter")
            await browser.close()
            log.info(f"Pre-warm OK - PDF test: {len(pdf)} bytes")
    except Exception as e:
        log.warning(f"Pre-warm fallo: {e}")

# ============================================================
# HELPER
# ============================================================

import tempfile

def fmt(val):
    """Formatea numero con separadores de miles (formato colombiano)"""
    if val is None:
        return "0"
    return f"{float(val):,.0f}".replace(",", ".")

def fmt_double(val):
    if val is None:
        return "0"
    return f"{float(val):,.2f}".replace(",", ".")

# ============================================================
# PDF GENERATION
# ============================================================

async def generate_pdf(data: dict) -> bytes:
    """Genera PDF usando Playwright Async API"""
    now = datetime.now()
    data.setdefault("dia", str(now.day))
    data.setdefault("mes", MESES[now.month - 1])
    data.setdefault("anio", str(now.year))

    # Calcular valores derivados
    vf = data.get("valor_final") or data.get("valor_total") or 0
    vp = data.get("valor_a_pagar") or 0
    data["saldo_a_pagar"] = float(vf) - float(vp)
    data["ibc"] = float(vp) * 0.4

    # Total planilla
    data["total_planilla"] = (
        float(data.get("eps_valor") or 0) +
        float(data.get("arl_valor") or 0) +
        float(data.get("ccf_valor") or 0) +
        float(data.get("afp_valor") or 0)
    )

    # Actividades: dividir por lineas
    actividades = data.get("actividades", "")
    if actividades and actividades.strip():
        data["actividades"] = [l.strip() for l in actividades.split("\n") if l.strip()]
    else:
        perfil = data.get("perfil", "")
        if perfil:
            data["actividades"] = [f"Actividades segun perfil contratado como {perfil}"]
        else:
            data["actividades"] = ["Actividades segun perfil contratado"]

    # Renderizar HTML
    template = templates.get_template("supervision.html")
    html = template.render(**data)

    if data.get("formato") == "html":
        return html.encode("utf-8")

    # Generar PDF con Playwright Async API
    # Usamos archivo temporal + page.goto() en vez de set_content()
    # porque goto() carga CSS y fuentes correctamente en Docker headless
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--font-render-hinting=none"]
            )
            page = await browser.new_page()
            # Escribir HTML a archivo temporal y navegar a el
            with tempfile.NamedTemporaryFile(
                suffix=".html", mode="w", delete=False, encoding="utf-8"
            ) as f:
                f.write(html)
                temp_path = f.name
            log.debug(f"HTML tempfile: {temp_path} ({len(html)} chars)")
            try:
                await page.goto(f"file://{temp_path}", wait_until="networkidle")
                await page.wait_for_timeout(1000)
                # Verificar que la pagina tenga contenido visible
                text_content = await page.evaluate("() => document.body.innerText")
                if text_content and text_content.strip():
                    log.debug(f"Contenido de pagina: {len(text_content.strip())} chars")
                else:
                    log.warning("Pagina sin contenido visible!")
                pdf = await page.pdf(
                    format="Letter",
                    print_background=True,
                    margin={"top": "0.3in", "right": "0.3in", "bottom": "0.3in", "left": "0.3in"}
                )
            finally:
                try:
                    os.unlink(temp_path)
                except:
                    pass
            await browser.close()
            log.info(f"PDF generado: {len(pdf)} bytes")
            return pdf
    except Exception as e:
        log.error(f"Playwright fallo: {e}", exc_info=True)
        log.warning("Sirviendo HTML como fallback")
        return html.encode("utf-8")

# ============================================================
# HEALTH
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()

# ============================================================
# ENDPOINTS
# ============================================================

@app.post("/api/v1/pdf/supervision")
async def generar_supervision(data: SupervisionPDFRequest):
    """Genera PDF de supervision de contrato"""
    pdf_bytes = await generate_pdf(data.model_dump())

    is_pdf = pdf_bytes[:4] == b"%PDF"
    media_type = "application/pdf" if is_pdf else "text/html; charset=utf-8"
    filename = f"supervision_{data.numero_contrato}.{'pdf' if is_pdf else 'html'}"

    return Response(
        content=pdf_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.post("/api/v1/pdf/resumen")
async def generar_resumen(data: SupervisionPDFRequest):
    """Genera PDF de supervision de contrato (mismo template por ahora)"""
    return await generar_supervision(data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)
