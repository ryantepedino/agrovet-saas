from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import io, re, sqlite3
from datetime import datetime
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np, cv2
import pytesseract
from paddleocr import PaddleOCR
import easyocr

# ==========================================================
# 🚀 Configuração principal da API
# ==========================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# 🧠 Motores OCR (Paddle + EasyOCR + Tesseract)
# ==========================================================
paddle_engine = PaddleOCR(use_angle_cls=True, lang='pt', show_log=False)
easy_engine = easyocr.Reader(['pt', 'en'], gpu=False)


# ==========================================================
# 🧩 Pré-processamento da imagem
# ==========================================================
def preprocess_image(image_bytes):
    """
    Melhora contraste, remove ruído e binariza imagem para melhorar OCR manuscrito.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("L")  # escala de cinza
    image = ImageEnhance.Contrast(image).enhance(2.5)         # aumenta contraste
    image = image.filter(ImageFilter.MedianFilter(size=3))    # suaviza ruído

    # binarização com OpenCV
    np_img = np.array(image)
    _, thresh = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)


# ==========================================================
# 🧠 Extração de texto híbrida
# ==========================================================
def extract_text_from_image(image_bytes):
    """
    Extrai texto da imagem com fallback híbrido e pré-processamento.
    """
    text = ""
    image = preprocess_image(image_bytes)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    processed_bytes = buf.getvalue()

    # 1️⃣ PaddleOCR
    try:
        results = paddle_engine.ocr(processed_bytes)
        if results and len(results[0]) > 0:
            text = " ".join([line[1][0] for line in results[0]])
    except Exception:
        text = ""

    # 2️⃣ EasyOCR
    if len(text.strip()) < 10 or not re.search(r"\d+%", text):
        try:
            result = easy_engine.readtext(np.array(image), detail=0)
            if result:
                text = " ".join(result)
        except Exception:
            pass

    # 3️⃣ Tesseract
    if len(text.strip()) < 10 or not re.search(r"\d+%", text):
        try:
            text = pytesseract.image_to_string(image, lang="por")
        except Exception:
            pass

    # 4️⃣ Limpeza final
    text = text.replace("\n", " ").replace("  ", " ").strip()
    return text


# ==========================================================
# 🧮 Extração de métricas (regex inteligente)
# ==========================================================
def parse_metrics(texto):
    """
    Usa expressões regulares para extrair métricas do texto OCR.
    """
    try:
        nome = re.search(r"(?i)(fazenda[:\- ]*)([A-Za-zÀ-ÿ0-9 ]+)", texto)
        prenhez = re.search(r"(?i)prenhe[z|s]?.*?(\d{1,3})\s*%", texto)
        concepcao = re.search(r"(?i)concep[cç][aã]o.*?(\d{1,3})\s*%", texto)
        servico = re.search(r"(?i)servi[cç]o.*?(\d{1,3})\s*%", texto)
        partos = re.search(r"(?i)parto[s]?.*?(\d{1,3})", texto)

        metrics = {
            "nome_da_fazenda": nome.group(2).strip() if nome else "Extraído via OCR",
            "taxa_prenhez": int(prenhez.group(1)) if prenhez else None,
            "taxa_concepcao": int(concepcao.group(1)) if concepcao else None,
            "taxa_servico": int(servico.group(1)) if servico else None,
            "partos_estimados": int(partos.group(1)) if partos else None,
        }
        return metrics
    except Exception as e:
        print(f"Erro ao extrair métricas: {e}")
        return {}


# ==========================================================
# 📤 Endpoint principal: /ocr_upload
# ==========================================================
@app.post("/ocr_upload")
async def ocr_upload(file: UploadFile = File(...)):
    """
    Recebe uma imagem, realiza OCR e salva resultados no SQLite.
    """
    try:
        image_bytes = await file.read()
        texto_extraido = extract_text_from_image(image_bytes)
        metrics = parse_metrics(texto_extraido)

        # --- Salva no banco SQLite ---
        try:
            conn = sqlite3.connect("backend/relatorios.db")
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS relatorios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_da_fazenda TEXT,
                    taxa_prenhez REAL,
                    taxa_concepcao REAL,
                    taxa_servico REAL,
                    partos_estimados REAL,
                    data TEXT
                )
            """)
            conn.commit()

            cur.execute("""
                INSERT INTO relatorios (
                    nome_da_fazenda, taxa_prenhez, taxa_concepcao,
                    taxa_servico, partos_estimados, data
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metrics.get("nome_da_fazenda"),
                metrics.get("taxa_prenhez"),
                metrics.get("taxa_concepcao"),
                metrics.get("taxa_servico"),
                metrics.get("partos_estimados"),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Erro ao salvar no banco: {e}")

        return {
            "status": "✅ OCR processado com sucesso!",
            "texto_extraido": texto_extraido,
            "métricas": metrics
        }

    except Exception as e:
        return {"erro": f"❌ Falha no processamento: {str(e)}"}


# ==========================================================
# 🔍 Endpoint de histórico (consulta SQLite)
# ==========================================================
@app.get("/relatorios")
def listar_relatorios():
    try:
        conn = sqlite3.connect("backend/relatorios.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM relatorios ORDER BY id DESC LIMIT 50")
        rows = cur.fetchall()
        conn.close()

        colunas = [
            "id", "nome_da_fazenda", "taxa_prenhez",
            "taxa_concepcao", "taxa_servico",
            "partos_estimados", "data"
        ]

        return [dict(zip(colunas, r)) for r in rows]
    except Exception as e:
        return {"erro": str(e)}
