import io
from datetime import date, datetime
from typing import Optional

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend import db

# ---------- setup ----------
st.set_page_config(page_title="AgroVet • Métricas", page_icon="🐄", layout="wide")

st.markdown(
    """
    <style>
    /* ======== Tema Visual AgroVet ======== */
    .css-1d391kg {background-color: #E8F6EF;}  /* fundo claro verde água */
    .stButton>button {
        background-color: #006D5B;
        color: white;
        border-radius: 8px;
        padding: 0.5em 1em;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #009688;
        color: white;
    }
    .stMetric .stMetricValue {
        color: #006D5B;
        font-weight: bold;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #004D40;
    }
    .stDataFrame {background-color: #FFFFFF;}
    </style>
    """,
    unsafe_allow_html=True,
)

db.init_db()

st.title("🐄 AgroVet • Painel de Métricas (sem OCR)")
st.caption("Lance métricas reprodutivas, acompanhe KPIs e gere relatórios (PDF/Excel).")

# ---------- formulário de lançamento ----------
with st.expander("➕ Lançar métricas da fazenda", expanded=True):
    col1, col2 = st.columns([2,1])
    with col1:
        nome = st.text_input("Nome da fazenda *", placeholder="Fazenda São João")
    with col2:
        data_lcto = st.date_input("Data *", value=date.today(), format="YYYY-MM-DD")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        taxa_prenhez = st.number_input("Taxa de prenhez (%)", min_value=0.0, max_value=100.0, step=0.1)
    with c2:
        taxa_concepcao = st.number_input("Taxa de concepção (%)", min_value=0.0, max_value=100.0, step=0.1)
    with c3:
        taxa_servico = st.number_input("Taxa de serviço (%)", min_value=0.0, max_value=100.0, step=0.1)
    with c4:
        partos = st.number_input("Partos estimados", min_value=0.0, step=1.0)

    left, right = st.columns([1,3])
    with left:
        if st.button("💾 Salvar lançamento", use_container_width=True):
            if not nome.strip():
                st.error("Informe o nome da fazenda.")
            else:
                rid = db.insert_relatorio(
                    nome_da_fazenda=nome.strip(),
                    data=str(data_lcto),
                    taxa_prenhez=float(taxa_prenhez) if taxa_prenhez else None,
                    taxa_concepcao=float(taxa_concepcao) if taxa_concepcao else None,
                    taxa_servico=float(taxa_servico) if taxa_servico else None,
                    partos_estimados=float(partos) if partos else None,
                )
                st.success(f"Lançamento salvo (ID {rid}).")

# ---------- filtros de histórico ----------
st.markdown("---")
st.subheader("📚 Histórico & Análises")

fcol1, fcol2, fcol3, fcol4 = st.columns([2,1,1,1])
with fcol1:
    filtro_nome = st.text_input("🔎 Buscar por fazenda")
with fcol2:
    d_ini = st.date_input("De", value=None, format="YYYY-MM-DD")
with fcol3:
    d_fim = st.date_input("Até", value=None, format="YYYY-MM-DD")
with fcol4:
    orden = st.selectbox("Ordenar", ["Mais recentes","Mais antigos","Nome (A-Z)"], index=0)

order_map = {"Mais recentes":"recentes","Mais antigos":"antigos","Nome (A-Z)":"nome"}

cols, rows = db.list_relatorios(
    search=(filtro_nome or None),
    date_from=(str(d_ini) if isinstance(d_ini, date) else None),
    date_to=(str(d_fim) if isinstance(d_fim, date) else None),
    order=order_map[orden],
    limit=500
)

df = pd.DataFrame(rows, columns=cols)

# ---------- KPIs ----------
k = db.kpis()
kcol1,kcol2,kcol3,kcol4,kcol5 = st.columns(5)
kcol1.metric("Registros", k["total_registros"])
kcol2.metric("Prenhez média", f"{k['media_prenhez']:.1f}%" if k['media_prenhez'] else "—")
kcol3.metric("Concepção média", f"{k['media_concepcao']:.1f}%" if k['media_concepcao'] else "—")
kcol4.metric("Serviço médio", f"{k['media_servico']:.1f}%" if k['media_servico'] else "—")
kcol5.metric("Partos médios", f"{k['media_partos']:.1f}" if k['media_partos'] else "—")

# ---------- tabela ----------
st.markdown("### 🧾 Registros")
if df.empty:
    st.info("Nenhum registro encontrado.")
else:
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- gráficos ----------
st.markdown("### 📈 Gráficos")

if not df.empty:
    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    gcol1, gcol2 = st.columns(2)

    # -------- Gráfico 1: Taxa de Prenhez --------
    with gcol1:
        fig, ax = plt.subplots(figsize=(6, 4))
        for fazenda, grp in df.groupby("nome_da_fazenda"):
            grp = grp.sort_values("data")
            if "taxa_prenhez" in grp and not grp["taxa_prenhez"].isna().all():
                ax.plot(
                    grp["data"],
                    grp["taxa_prenhez"],
                    marker="o",
                    linestyle="-",
                    label=fazenda,
                )
        ax.set_title("Evolução da taxa de prenhez", fontsize=11, pad=12)
        ax.set_xlabel("Data")
        ax.set_ylabel("%")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=45, ha="right")  # rotação de 45° para evitar sobreposição
        plt.tight_layout()
        ax.legend(fontsize=8, loc="best")
        st.pyplot(fig)

    # -------- Gráfico 2: Taxa de Concepção --------
    with gcol2:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        for fazenda, grp in df.groupby("nome_da_fazenda"):
            grp = grp.sort_values("data")
            if "taxa_concepcao" in grp and not grp["taxa_concepcao"].isna().all():
                ax2.plot(
                    grp["data"],
                    grp["taxa_concepcao"],
                    marker="o",
                    linestyle="-",
                    label=fazenda,
                )
        ax2.set_title("Evolução da taxa de concepção", fontsize=11, pad=12)
        ax2.set_xlabel("Data")
        ax2.set_ylabel("%")
        ax2.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=45, ha="right")  # rotação aplicada aqui também
        plt.tight_layout()
        ax2.legend(fontsize=8, loc="best")
        st.pyplot(fig2)


# ---------- exportações ----------
st.markdown("### 📤 Exportar")

colx, coly = st.columns(2)

with colx:
    if not df.empty:
        buf_xlsx = io.BytesIO()
        with pd.ExcelWriter(buf_xlsx, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Relatórios")
        buf_xlsx.seek(0)
        st.download_button(
            "⬇️ Baixar Excel",
            data=buf_xlsx,
            file_name=f"agrovet_relatorios_{datetime.now():%Y%m%d_%H%M}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.button("⬇️ Baixar Excel", disabled=True)

with coly:
    if not df.empty:
        # Gera PDF simples com ReportLab
        pdf_bytes = io.BytesIO()
        c = canvas.Canvas(pdf_bytes, pagesize=A4)
        w, h = A4
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, h-40, "Relatório AgroVet")
        c.setFont("Helvetica", 10)
        c.drawString(40, h-60, f"Gerado em: {datetime.now():%d/%m/%Y %H:%M}")

        # Tabela resumida (primeiros 25)
        y = h-90
        headers = ["ID","Fazenda","Data","Prenhez","Concepção","Serviço","Partos"]
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, " | ".join(headers))
        c.setFont("Helvetica", 9)
        y -= 16
        for _, row in df.head(25).iterrows():
            line = f"{row['id']} | {row['nome_da_fazenda']} | {row['data']:%Y-%m-%d} | " \
                   f"{row['taxa_prenhez'] if pd.notna(row['taxa_prenhez']) else '—'} | " \
                   f"{row['taxa_concepcao'] if pd.notna(row['taxa_concepcao']) else '—'} | " \
                   f"{row['taxa_servico'] if pd.notna(row['taxa_servico']) else '—'} | " \
                   f"{row['partos_estimados'] if pd.notna(row['partos_estimados']) else '—'}"
            c.drawString(40, y, line)
            y -= 14
            if y < 60:
                c.showPage()
                y = h-40
        c.showPage()
        c.save()
        pdf_bytes.seek(0)

        st.download_button(
            "⬇️ Baixar PDF",
            data=pdf_bytes,
            file_name=f"agrovet_relatorio_{datetime.now():%Y%m%d_%H%M}.pdf",
            mime="application/pdf",
        )
    else:
        st.button("⬇️ Baixar PDF", disabled=True)

st.markdown("---")
st.caption("Pronto para produção: SQLite + Excel/PDF + Gráficos. OCR pode ser plugado depois (Gemini/GPT-4o Vision).")
