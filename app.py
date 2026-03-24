import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.title("Dashboard - Controle de Presença Board")

# =========================
# LEITURA GOOGLE SHEETS
# =========================
url = "https://docs.google.com/spreadsheets/d/1LWPHqqmLCaqHjCGrLADyR4jPRVK05CxnQQNEheHmAZ4/export?format=csv"

df = pd.read_csv(url)

# =========================
# AJUSTE DA ESTRUTURA
# =========================
df = df.iloc[4:].reset_index(drop=True)

df.columns = df.iloc[0]
df = df[1:].reset_index(drop=True)

# REMOVE COLUNAS VAZIAS
df = df.loc[:, df.columns.notna()]

# REMOVE DUPLICADAS
df = df.loc[:, ~df.columns.duplicated()]

# LIMPA NOMES
df.columns = df.columns.astype(str).str.strip().str.upper()

# =========================
# IDENTIFICA COLUNAS
# =========================
def find_col(keyword):
    for col in df.columns:
        if keyword in col:
            return col
    return None

def find_obs(numero):
    for col in df.columns:
        if f"{numero}º" in col or f"{numero} ENCONTRO" in col:
            return col
    return None

col_nome = find_col("NOME")
col_turma = find_col("TURMA")

col_obs1 = find_obs(1)
col_obs2 = find_obs(2)
col_obs3 = find_obs(3)

# =========================
# CRIA COLUNAS PADRÃO
# =========================
df["nome"] = df[col_nome] if col_nome else ""
df["turma"] = df[col_turma] if col_turma else ""
df["obs1"] = df[col_obs1] if col_obs1 else ""
df["obs2"] = df[col_obs2] if col_obs2 else ""
df["obs3"] = df[col_obs3] if col_obs3 else ""

# =========================
# BASE EDITÁVEL
# =========================
st.subheader("Base de Dados")
df = st.data_editor(df, num_rows="dynamic")

# =========================
# TRATAMENTO TURMA / EDIÇÃO
# =========================
df["turma"] = df["turma"].astype(str).str.strip()

split_cols = df["turma"].str.split(" - ", n=1, expand=True)

if split_cols.shape[1] == 2:
    df["turma_nome"] = split_cols[0]
    df["edicao"] = split_cols[1]
else:
    df["turma_nome"] = df["turma"]
    df["edicao"] = "Não identificado"

# =========================
# REPOSIÇÃO (ROBUSTO)
# =========================
def check_reposicao(row):
    textos = [
        str(row.get("obs1", "")).lower(),
        str(row.get("obs2", "")).lower(),
        str(row.get("obs3", "")).lower()
    ]

    palavras_chave = [
        "repos", "reposição", "remarc",
        "reagend", "repôs", "reposicao"
    ]

    return any(
        any(p in t for p in palavras_chave)
        for t in textos
    )

df["reposicao"] = df.apply(check_reposicao, axis=1)

# DEBUG (pode remover depois)
st.write("Total de reposições detectadas:", df["reposicao"].sum())

# =========================
# KPIs GERAIS
# =========================
st.markdown("## 📊 Visão Geral")

col1, col2, col3 = st.columns(3)

total = len(df)
total_repos = df["reposicao"].sum()
taxa = (total_repos / total * 100) if total > 0 else 0

col1.metric("Total de Participantes", total)
col2.metric("Total de Reposições", total_repos)
col3.metric("Taxa de Reposição", f"{taxa:.1f}%")

st.divider()

# =========================
# ANÁLISES
# =========================
st.markdown("## 📈 Análises")

st.subheader("Participantes por Turma")
participantes = df.groupby("turma_nome")["nome"].count()
st.bar_chart(participantes)

st.divider()

st.subheader("Reposições por Turma")
reposicoes = df[df["reposicao"] == True]
reposicoes_por_turma = reposicoes.groupby("turma_nome")["nome"].count()
st.bar_chart(reposicoes_por_turma)

st.divider()

# =========================
# FILTROS
# =========================
st.sidebar.title("Filtros")

lista_edicoes = sorted(df["edicao"].dropna().unique())
edicao = st.sidebar.selectbox("Selecione a edição", lista_edicoes)

df_edicao = df[df["edicao"] == edicao]

lista_turmas = sorted(df_edicao["turma_nome"].dropna().unique())
turma = st.sidebar.selectbox("Selecione a turma", lista_turmas)

df_turma = df_edicao[df_edicao["turma_nome"] == turma]

# =========================
# KPIs DA TURMA
# =========================
st.markdown(f"## 📌 Resumo: {edicao} | {turma}")

col1, col2, col3 = st.columns(3)

total_turma = len(df_turma)
reposicoes_turma_count = df_turma["reposicao"].sum()
taxa_turma = (reposicoes_turma_count / total_turma * 100) if total_turma > 0 else 0

col1.metric("Participantes", total_turma)
col2.metric("Reposições", reposicoes_turma_count)
col3.metric("Taxa de Reposição", f"{taxa_turma:.1f}%")

st.divider()

# =========================
# LISTA
# =========================
st.subheader("Reposições da Turma")

reposicoes_turma = df_turma[df_turma["reposicao"] == True]

if len(reposicoes_turma) > 0:
    st.dataframe(
        reposicoes_turma[["nome", "turma_nome", "edicao", "obs1", "obs2", "obs3"]],
        use_container_width=True
    )
else:
    st.info("Nenhuma reposição encontrada")