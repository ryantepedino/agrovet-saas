from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from loguru import logger
import tempfile
import shutil
import os

# Importa o pipeline e o gerador de PDF
from ai.ocr_pipeline import run_pipeline
from ai.pdf_report import gerar_pdf_relatorio

router = APIRouter()

@router.post("/ocr_upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Endpoint que recebe imagem, executa OCR neural + parser
    e gera automaticamente o PDF.
    """
    tmp_path = None

    try:
        # Salvar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        logger.info(f"📥 Imagem recebida: {file.filename}")
        logger.info(f"📂 Caminho temporário: {tmp_path}")

        # Executar pipeline completo
        result = run_pipeline(tmp_path)
        logger.info(f"🔍 Retorno pipeline: {result}")

        # ✅ Adaptação: aceita ambos formatos (com ou sem 'data')
        metrics = result.get("data", result.get("metrics", {}))
        conf = result.get("confidence", result.get("conf", 0))

        # Verifica se há métricas válidas
        if metrics and isinstance(metrics, dict):
            # Gera o PDF automaticamente
            nome_pdf = gerar_pdf_relatorio(metrics)
            logger.info(f"📄 Relatório PDF gerado: {nome_pdf}")

            return JSONResponse(
                {
                    "ok": True,
                    "message": "Processado com sucesso!",
                    "metrics": metrics,
                    "confidence": conf,
                    "pdf": nome_pdf,
                }
            )

        # Se não tiver métricas
        else:
            logger.warning("⚠️ Nenhum dado válido retornado pelo OCR.")
            return JSONResponse(
                {"ok": False, "error": "Nenhum dado reconhecido na imagem."}
            )

    except Exception as e:
        logger.error(f"❌ Erro no upload OCR: {e}")
        return JSONResponse({"ok": False, "error": str(e)})

    finally:
        # Limpeza segura do arquivo temporário
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
