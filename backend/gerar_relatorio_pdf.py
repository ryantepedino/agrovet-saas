from fpdf import FPDF
import json
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Relatorio AgroVet - OCR + IA", ln=True, align="C")
        self.ln(5)

def gerar_relatorio_pdf(dados_ocr: dict, nome_arquivo="relatorio_agrovet.pdf"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Data de Geracao: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "METRICAS EXTRAIDAS:", ln=True)
    pdf.set_font("Arial", "", 12)

    metricas = dados_ocr.get("métricas", {})
    for chave, valor in metricas.items():
        pdf.cell(0, 10, f"{chave.replace('_', ' ').capitalize()}: {valor}", ln=True)

    pdf.ln(8)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ANALISE INTELIGENTE (IA MOCK):", ln=True)
    pdf.set_font("Arial", "", 12)
    texto_ia = (
        "Com base nas métricas detectadas via OCR, o sistema identificou que a taxa "
        "de prenhez e concepção está dentro dos parâmetros esperados. "
        "É recomendável revisar o manejo reprodutivo e acompanhar o histórico de partos "
        "para otimização de resultados futuros."
    )
    pdf.multi_cell(0, 8, texto_ia)

    pdf.output(nome_arquivo)
    print(f"✅ Relatório gerado: {nome_arquivo}")

if __name__ == "__main__":
    with open("resultado_ocr_mock.json", "r") as f:
        dados = json.load(f)
    gerar_relatorio_pdf(dados)
