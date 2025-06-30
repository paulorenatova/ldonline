import streamlit as st
import pandas as pd
import os

# ===== Caminhos =====
ARQ_PROJETOS = "projetos.csv"
ARQ_DOCS = "lista_documentos.csv"
ARQ_RAMAIS = "ramais.csv"
ARQ_DISCIPLINAS = "disciplinas.csv"
ARQ_TIPOS = "tipos_documento.csv"
ARQ_FASES = "fases.csv"

# ===== Colunas padrão =====
COLS_PROJ = ["ID SAP", "Projeto", "Ramal", "Km Inicial", "Fase"]
COLS_DOCS = ["ID SAP", "Disciplina", "Tipo", "Sequencial", "Código", "Descrição", "Código Projetista"]

# ===== Utilitários =====
def carregar_csv(caminho, colunas=None):
    if os.path.exists(caminho):
        df = pd.read_csv(caminho, dtype=str).fillna("")
        if colunas:
            for col in colunas:
                if col not in df.columns:
                    df[col] = ""
            return df[colunas]
        return df
    return pd.DataFrame(columns=colunas if colunas else [], dtype=str)

def salvar_csv(df, caminho):
    df.to_csv(caminho, index=False)

def proximo_sequencial(df_docs, id_sap, disciplina):
    qtd = df_docs[(df_docs["ID SAP"] == id_sap) & (df_docs["Disciplina"] == disciplina)].shape[0]
    return f"{qtd + 1:03}"

def montar_codigo(row_proj, row_doc):
    return "-".join([
        row_proj["ID SAP"], row_proj["Ramal"], row_proj["Km Inicial"], row_proj["Fase"],
        row_doc["Disciplina"], row_doc["Tipo"], row_doc["Sequencial"]
    ])

# ===== Carregar listas externas =====
def carregar_lista_externa(caminho, colunas):
    if not os.path.exists(caminho):
        st.error(f"Arquivo {caminho} não encontrado.")
        st.stop()
    df = pd.read_csv(caminho, dtype=str).fillna("")
    if not set(colunas).issubset(df.columns):
        st.error(f"Colunas inválidas no arquivo {caminho}.")
        st.stop()
    return df

# Dados externos
df_ramais = carregar_lista_externa(ARQ_RAMAIS, ["descricao_ramal", "sigla_ramal"])
df_disc = carregar_lista_externa(ARQ_DISCIPLINAS, ["sigla_disciplina", "nome_disciplina"])
df_tipo = carregar_lista_externa(ARQ_TIPOS, ["sigla_tipo", "nome_tipo"])
df_fase = carregar_lista_externa(ARQ_FASES, ["descricao_fase", "sigla_fase"])

SIGLA_PARA_DESC_RAMAL = dict(zip(df_ramais["sigla_ramal"], df_ramais["descricao_ramal"]))
SIGLA_PARA_DESC_DISC = dict(zip(df_disc["sigla_disciplina"], df_disc["nome_disciplina"]))
SIGLA_PARA_DESC_TIPO = dict(zip(df_tipo["sigla_tipo"], df_tipo["nome_tipo"]))
SIGLA_PARA_DESC_FASE = dict(zip(df_fase["sigla_fase"], df_fase["descricao_fase"]))

# ===== Dados principais =====
df_proj = carregar_csv(ARQ_PROJETOS, COLS_PROJ)
df_docs = carregar_csv(ARQ_DOCS, COLS_DOCS)

st.set_page_config("Gestor de Projetos e LD", layout="wide")
pagina = st.sidebar.radio("Navegação", ["Projetos", "Documentos"])

# ******************************************************************
# PROJETOS
# ******************************************************************
if pagina == "Projetos":
    st.title("📁 Cadastro de Projetos")

    with st.form("form_proj", clear_on_submit=True):
        id_sap = st.text_input("ID SAP (ex: CC00001)").strip()
        nome = st.text_input("Nome do Projeto")
        ramal = st.selectbox("Ramal", df_ramais["sigla_ramal"])
        km_ini = st.text_input("Km Inicial", max_chars=10)
        fase = st.selectbox("Fase", df_fase["sigla_fase"])
        if st.form_submit_button("Salvar Projeto"):
            if id_sap in df_proj["ID SAP"].values:
                st.warning("ID SAP já existe.")
            else:
                df_proj.loc[len(df_proj)] = [id_sap, nome, ramal, km_ini, fase]
                salvar_csv(df_proj, ARQ_PROJETOS)
                st.success("Projeto salvo.")
                st.rerun()

    st.divider()
    st.subheader("📋 Projetos Cadastrados")
    for _, row in df_proj.iterrows():
        c1, c2 = st.columns([8, 1])
        info = f"{SIGLA_PARA_DESC_RAMAL.get(row['Ramal'], row['Ramal'])}, Km {row['Km Inicial']}, Fase {SIGLA_PARA_DESC_FASE.get(row['Fase'], row['Fase'])}"
        c1.write(f"**{row['ID SAP']}** – {row['Projeto']} | {info}")
        if c2.button("🗑️", key=f"del_{row['ID SAP']}"):
            df_proj = df_proj[df_proj["ID SAP"] != row["ID SAP"]]
            df_docs = df_docs[df_docs["ID SAP"] != row["ID SAP"]]
            salvar_csv(df_proj, ARQ_PROJETOS)
            salvar_csv(df_docs, ARQ_DOCS)
            st.success("Projeto e documentos removidos.")
            st.rerun()

# ******************************************************************
# DOCUMENTOS
# ******************************************************************
else:
    st.title("📑 Lista de Documentos")

    if df_proj.empty:
        st.warning("Cadastre um projeto antes de inserir documentos.")
        st.stop()

    projeto_str = st.sidebar.selectbox("Selecione o Projeto", df_proj["ID SAP"] + " - " + df_proj["Projeto"])
    id_sel = projeto_str.split(" - ")[0]
    proj_sel = df_proj[df_proj["ID SAP"] == id_sel].iloc[0]

    st.markdown(f"**Projeto ativo: `{id_sel}` – {proj_sel['Projeto']}**")

    # Cadastro de novo documento
    with st.expander("➕ Novo Documento", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            disciplina = st.selectbox("Disciplina", df_disc["sigla_disciplina"])
            tipo = st.selectbox("Tipo de Arquivo", df_tipo["sigla_tipo"])
        with col2:
            descricao = st.text_input("Descrição")
            cod_proj = st.text_input("Código Projetista")

        if st.button("Salvar Documento"):
            sequencial = proximo_sequencial(df_docs, id_sel, disciplina)
            linha = {
                "ID SAP": id_sel,
                "Disciplina": disciplina,
                "Tipo": tipo,
                "Sequencial": sequencial,
                "Descrição": descricao,
                "Código Projetista": cod_proj
            }
            linha["Código"] = montar_codigo(proj_sel, linha)
            df_docs.loc[len(df_docs)] = linha
            salvar_csv(df_docs, ARQ_DOCS)
            st.success(f"Documento {linha['Código']} salvo.")
            st.rerun()

    # Lista com filtros
    st.subheader("📋 Lista de documentos")
    docs_proj = df_docs[df_docs["ID SAP"] == id_sel].copy()

    colf1, colf2 = st.columns(2)
    with colf1:
        filtro_disc = st.selectbox("Filtrar por Disciplina", ["Todos"] + df_disc["sigla_disciplina"].tolist())
    with colf2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos"] + df_tipo["sigla_tipo"].tolist())

    if filtro_disc != "Todos":
        docs_proj = docs_proj[docs_proj["Disciplina"] == filtro_disc]
    if filtro_tipo != "Todos":
        docs_proj = docs_proj[docs_proj["Tipo"] == filtro_tipo]

    if docs_proj.empty:
        st.info("Nenhum documento encontrado com os filtros aplicados.")
    else:
        docs_proj.reset_index(drop=True, inplace=True)
        sel_idx = st.radio("Selecione um documento para editar ou excluir:",
                           options=docs_proj.index,
                           format_func=lambda i: docs_proj.at[i, "Código"],
                           horizontal=True)

        st.table(docs_proj)

        with st.expander("✏️ Editar Documento"):
            row = docs_proj.loc[sel_idx]
            nova_desc = st.text_input("Nova Descrição", value=row["Descrição"], key="desc_edit")
            novo_cp = st.text_input("Novo Código Projetista", value=row["Código Projetista"], key="cp_edit")

            if st.button("Salvar Edição"):
                idx_global = df_docs[(df_docs["ID SAP"] == id_sel) & (df_docs["Código"] == row["Código"])].index[0]
                df_docs.at[idx_global, "Descrição"] = nova_desc
                df_docs.at[idx_global, "Código Projetista"] = novo_cp
                salvar_csv(df_docs, ARQ_DOCS)
                st.success("Documento atualizado.")
                st.rerun()

        if st.button("🗑️ Excluir Documento"):
            idx_global = df_docs[(df_docs["ID SAP"] == id_sel) & (df_docs["Código"] == docs_proj.at[sel_idx, "Código"])].index[0]
            df_docs.drop(idx_global, inplace=True)
            salvar_csv(df_docs, ARQ_DOCS)
            st.success("Documento excluído.")
            st.rerun()
