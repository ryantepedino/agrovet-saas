from fpdf import FPDF
import json
from datetime import datetime
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Relatorio AgroVet - OCR + IA", ln=True, align="C")
        self.ln(5)

def gerar_relatorio_pdf(dados_ocr: dict, nome_arquivo="relatorio_agrovet.pdf"):
    from openai import OpenAI

    # 🔗 Detecta se há API local (Ollama/LM Studio) ou OpenAI oficial
    base_url = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
    api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
    client = OpenAI(api_key=api_key, base_url=base_url)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Data de Geracao: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "METRICAS EXTRAIDAS:", ln=True)
    pdf.set_font("Arial", "", 12)

    metricas = dados_ocr.get("métricas", {})
    texto_metricas = ""
    for chave, valor in metricas.items():
        linha = f"{chave.replace('_', ' ').capitalize()}: {valor}"
        pdf.cell(0, 10, linha, ln=True)
        texto_metricas += linha + "\n"

    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ANALISE INTELIGENTE (IA REAL):", ln=True)
    pdf.set_font("Arial", "", 12)

    # 🧠 Geração da análise via modelo
    prompt = f"""
    Você é um assistente agropecuário. Analise os seguintes dados zootécnicos e gere um breve parecer técnico:
    {texto_metricas}

    Diga:
    - Se os resultados estão dentro do esperado;
    - O que pode estar bom ou ruim;
    - Recomendações de manejo e observações.
    """

    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )
        texto_ia = resposta.choices[0].message.content.strip()
    except Exception as e:
        texto_ia = f"[ERRO] Não foi possível gerar análise via IA. Detalhe: {e}"

    pdf.multi_cell(0, 8, texto_ia)
    pdf.output(nome_arquivo)
    print(f"✅ Relatório IA gerado: {nome_arquivo}")

if __name__ == "__main__":
    with open("resultado_ocr_mock.json", "r") as f:
        dados = json.load(f)
    gerar_relatorio_pdf(dados)
