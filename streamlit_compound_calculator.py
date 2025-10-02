import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import json
import os

# -----------------------------
# Persistência com JSON
# -----------------------------
FILE_PATH = "cenarios.json"

def carregar_cenarios():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            return json.load(f)
    return {}

def salvar_cenarios(cenarios):
    with open(FILE_PATH, "w") as f:
        json.dump(cenarios, f, indent=4)

cenarios = carregar_cenarios()

# -----------------------------
# Configuração da página
# -----------------------------
st.set_page_config(page_title="Calculadora de Juros Compostos", layout="wide")

st.title("📈 Calculadora de Juros Compostos para Investimentos")

# -----------------------------
# Sidebar - Inputs
# -----------------------------
st.sidebar.header("⚙️ Parâmetros do cenário")

nome_cenario = st.sidebar.text_input("Nome do cenário (para salvar/reabrir)")

valor_inicial = st.sidebar.number_input("Valor inicial (R$)", 0.0, step=100.0)
aporte_mensal = st.sidebar.number_input("Aporte mensal (R$)", 0.0, step=100.0)
taxa_anual = st.sidebar.number_input("Taxa de juros (% a.a.)", 0.0, step=0.1)
anos = st.sidebar.slider("Horizonte (anos)", 1, 50, 10)
cdi_medio = st.sidebar.number_input("CDI médio estimado (% a.a.)", 0.0, step=0.1)

# -----------------------------
# Salvar/Carregar/Excluir cenários
# -----------------------------
st.sidebar.subheader("📂 Gestão de cenários")

if st.sidebar.button("💾 Salvar cenário"):
    if nome_cenario.strip():
        cenarios[nome_cenario] = {
            "valor_inicial": valor_inicial,
            "aporte_mensal": aporte_mensal,
            "taxa_anual": taxa_anual,
            "anos": anos,
            "cdi_medio": cdi_medio,
        }
        salvar_cenarios(cenarios)
        st.sidebar.success(f"Cenário '{nome_cenario}' salvo!")
    else:
        st.sidebar.error("Digite um nome para salvar o cenário.")

opcao = st.sidebar.selectbox("Selecione um cenário existente", [""] + list(cenarios.keys()))

colA, colB = st.sidebar.columns(2)
with colA:
    if opcao:
        if st.button("📥 Carregar"):
            dados = cenarios[opcao]
            valor_inicial = dados["valor_inicial"]
            aporte_mensal = dados["aporte_mensal"]
            taxa_anual = dados["taxa_anual"]
            anos = dados["anos"]
            cdi_medio = dados.get("cdi_medio", 0.0)
            st.sidebar.success(f"Cenário '{opcao}' carregado!")

with colB:
    if opcao:
        if st.button("🗑️ Excluir"):
            del cenarios[opcao]
            salvar_cenarios(cenarios)
            st.sidebar.warning(f"Cenário '{opcao}' excluído!")

# -----------------------------
# Cálculo
# -----------------------------
meses = anos * 12
taxa_mensal = (1 + taxa_anual/100) ** (1/12) - 1
cdi_mensal = (1 + cdi_medio/100) ** (1/12) - 1

saldos, aportes, ganhos, cdi_ref = [], [], [], []
saldo = valor_inicial
saldo_cdi = valor_inicial

for m in range(meses+1):
    saldos.append(saldo)
    aportes.append(valor_inicial + aporte_mensal*m)
    ganhos.append(saldo - (valor_inicial + aporte_mensal*m))
    cdi_ref.append(saldo_cdi)
    if m < meses:
        saldo = saldo*(1+taxa_mensal) + aporte_mensal
        saldo_cdi = saldo_cdi*(1+cdi_mensal) + aporte_mensal

df = pd.DataFrame({
    "Mês": list(range(meses+1)),
    "Saldo acumulado": saldos,
    "Total aportado": aportes,
    "Ganhos": ganhos,
    "Saldo CDI": cdi_ref
})

# -----------------------------
# Resultados - gráficos
# -----------------------------
st.subheader("📊 Evolução do patrimônio")
fig = px.line(
    df,
    x="Mês",
    y=["Saldo acumulado", "Saldo CDI"],
    labels={"value":"R$","variable":"Cenário"},
    title="Comparativo: Investimento vs CDI"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📑 Tabela detalhada")
st.dataframe(df, use_container_width=True)

# -----------------------------
# Resumo final
# -----------------------------
st.subheader("📌 Resumo do cenário")
colR1, colR2, colR3 = st.columns(3)
with colR1:
    st.metric("Valor final", f"R$ {saldos[-1]:,.2f}")
with colR2:
    st.metric("Total aportado", f"R$ {aportes[-1]:,.2f}")
with colR3:
    st.metric("Ganhos", f"R$ {ganhos[-1]:,.2f}")

# -----------------------------
# Calculadora reversa
# -----------------------------
st.subheader("🎯 Calculadora reversa: Quanto aportar para atingir uma meta?")
meta_final = st.number_input("Meta financeira (R$)", 0.0, step=1000.0)

if meta_final > 0:
    # fórmula: FV = P*(1+i)^n + PMT*(((1+i)^n -1)/i)
    n = meses
    i = taxa_mensal
    FV = meta_final
    P = valor_inicial
    if i > 0:
        PMT = (FV - P*(1+i)**n) / (((1+i)**n - 1)/i)
    else:
        PMT = (FV - P) / n
    if PMT < 0:
        st.error("Com os parâmetros atuais, a meta já é atingida sem aportes adicionais.")
    else:
        # st.success(f"Você precisará aportar aproximadamente R$ {PMT:,.2f} por mês para atingir a meta de R$ {meta_final:,.2f}.")
        st.markdown(
            f"<div style='background-color:#d4edda;padding:10px;border-radius:5px;color:#155724;'>"
            f"Você precisará aportar aproximadamente <b>R$ {PMT:,.2f}</b> por mês para atingir a meta de <b>R$ {meta_final:,.2f}</b>."
            f"</div>",
            unsafe_allow_html=True
        )


# -----------------------------
# Exportação CSV
# -----------------------------
st.subheader("📤 Exportar resultados")
st.download_button(
    "Baixar tabela em CSV",
    df.to_csv(index=False).encode("utf-8"),
    "simulacao.csv",
    "text/csv",
    key="download-csv"
)