# backend/pdf_report.py
from fpdf import FPDF
from datetime import datetime
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Relatorio AgroVet - OCR + IA", ln=True, align="C")
        self.ln(5)

def _analise_ia_texto(metrics: dict, source_text: str) -> str:
    """
    Gera análise dinâmica. Usa OpenAI se OPENAI_API_KEY estiver setada,
    caso contrário gera um comentário heurístico simples.
    """
    farm = metrics.get("nome_da_fazenda", "Fazenda")
    prenhez = metrics.get("taxa_prenhez")
    concepcao = metrics.get("taxa_concepcao")
    servico = metrics.get("taxa_servico")
    partos = metrics.get("partos_estimados")

    # Heurística simples (sem API):
    base = [f"Fazenda: {farm}."]
    if prenhez is not None:
        base.append(f"Taxa de prenhez: {prenhez}%.")
    if concepcao is not None:
        base.append(f"Taxa de concepcao: {concepcao}%.")
    if servico is not None:
        base.append(f"Taxa de servico: {servico}%.")
    if partos is not None:
        base.append(f"Partos estimados: {partos}.")

    recomend = []
    if isinstance(prenhez, (int, float)):
        if prenhez >= 75:
            recomend.append("Prenhez em bom patamar. Manter protocolo e sanidade.")
        else:
            recomend.append("Prenhez abaixo do ideal. Avaliar nutrição, cio e protocolos.")
    if isinstance(concepcao, (int, float)) and concepcao < 70:
        recomend.append("Concepcao moderada/baixa. Verificar manejo de IA e condição corporal.")
    if isinstance(servico, (int, float)) and servico < 80:
        recomend.append("Taxa de servico pode melhorar com detecção de cio e calendário mais rígido.")

    texto_heuristico = " ".join(base + ["Recomendações:"] + recomend) if recomend else " ".join(base)

    # Tenta usar OpenAI se houver chave
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return texto_heuristico

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        prompt = f"""
        Você é um zootecnista. Analise os indicadores abaixo e gere um parecer curto, claro e acionável:
        {metrics}

        Texto capturado via OCR: {source_text}
        """
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return texto_heuristico

def gerar_relatorio_pdf(metrics: dict, source_text: str, out_path: str):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Data de Geracao: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)

    # Métricas
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "METRICAS EXTRAIDAS:", ln=True)
    pdf.set_font("Arial", "", 12)

    show = [
        ("Nome da fazenda", metrics.get("nome_da_fazenda", "—")),
        ("Taxa de prenhez (%)", metrics.get("taxa_prenhez", "—")),
        ("Taxa de concepcao (%)", metrics.get("taxa_concepcao", "—")),
        ("Taxa de servico (%)", metrics.get("taxa_servico", "—")),
        ("Partos estimados", metrics.get("partos_estimados", "—")),
    ]
    for k, v in show:
        pdf.cell(0, 10, f"{k}: {v}", ln=True)

    pdf.ln(6)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "ANALISE:", ln=True)
    pdf.set_font("Arial", "", 12)
    texto = _analise_ia_texto(metrics, source_text)
    pdf.multi_cell(0, 8, texto)

    pdf.output(out_path)
    return out_path
