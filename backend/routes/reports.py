import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from loguru import logger

from backend.db import init_db, save_report, list_reports, get_pdf_path
from ai.pdf_dashboard import gerar_pdf

router = APIRouter()

@router.on_event("startup")
def _startup():
    init_db()
    logger.info("SQLite inicializado.")

@router.post("/reports/save")
async def reports_save(payload: dict):
    """
    Corpo esperado:
    {
      "metrics": {...},
      "raw_text": "texto ocr"
    }
    Gera o PDF, salva no SQLite + filesystem e retorna o id.
    """
    metrics = payload.get("metrics") or {}
    raw_text = payload.get("raw_text") or ""
    farm_name = str(metrics.get("nome_da_fazenda", "Fazenda"))

    try:
        pdf_bytes = gerar_pdf(metrics)
        report_id = save_report(farm_name=farm_name, metrics=metrics, ocr_text=raw_text, pdf_bytes=pdf_bytes)
        return {"ok": True, "id": report_id}
    except Exception as e:
        logger.exception("Falha ao salvar relatório")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {e}")

@router.get("/reports/list")
async def reports_list():
    return {"ok": True, "items": list_reports()}

@router.get("/reports/{report_id}/pdf")
async def reports_pdf(report_id: int):
    path = get_pdf_path(report_id)
    if not path:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    try:
        with open(path, "rb") as f:
            data = f.read()
        return StreamingResponse(io.BytesIO(data), media_type="application/pdf",
                                 headers={"Content-Disposition": f'attachment; filename="report_{report_id}.pdf"'})
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo PDF não encontrado")
