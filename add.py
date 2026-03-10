import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go
from io import BytesIO

# 1. CONEXÃO
def buscar_dados():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    df = pd.DataFrame(wks.get_all_records())
    
    # Organizar nomes das colunas por posição
    df.columns.values[0] = "timestamp"
    df.columns.values[1] = "nome"
    df.columns.values[2] = "empresa"
    df.columns.values[3] = "nps_nota"
    df.columns.values[4] = "nps_motivo"
    
    crit_nomes = ['Clareza', 'Prazos', 'Comunicação', 'Cordialidade', 'Custo']
    for i, nome in enumerate(crit_nomes):
        df.columns.values[5 + i] = nome
    
    setores = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
    for i, nome in enumerate(setores):
        df.columns.values[10 + (i*2)] = f"Nota_{nome}"
        
    return df, setores

# Função auxiliar para converter o Excel em memória (sem salvar arquivo no servidor)
def converter_para_excel(df_download):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_download.to_excel(writer, index=False, sheet_name='Respostas')
    return output.getvalue()

st.set_page_config(page_title="Escrita Contabilidade", layout="wide")

# ESTILO CSS
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 35px; color: #1f3b5c; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef; }
    [data-testid="stSidebar"] { background-color: #f8f9fb; }
    </style>
    """, unsafe_allow_html=True)

try:
    dados_brutos, setores_lista = buscar_dados()
    df = dados_brutos.copy()

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        try:
            st.image("Logo Escrita.png", width=200)
        except:
            st.write("### ESCRITA CONTABILIDADE")
            
        st.title("Filtros")
        setor_selecionado = st.selectbox("Filtrar por Setor", ["Todos"] + setores_lista)
        
        # APLICAÇÃO DO FILTRO
        if setor_selecionado != "Todos":
            col_setor = f"Nota_{setor_selecionado}"
            df = df[df[col_setor] != ""].copy()

        st.divider()
        st.write("### Ações")
        
        # --- LÓGICA DO BOTÃO DE DOWNLOAD ---
        # Preparamos o arquivo Excel com os dados (respeitando o filtro selecionado)
        excel_data = converter_para_excel(df)
        
        st.download_button(
            label="📥 Baixar em Excel",
            data=excel_data,
            file_name=f"pesquisa_satisfacao_{setor_selecionado}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # --- TÍTULO ---
    st.markdown("# 📊 Dashboard de Performance NPS Smart")
    
    # Conversão de números
    df['nps_nota'] = pd.to_numeric(df['nps_nota'], errors='coerce')
    crit_colunas = ['Clareza', 'Prazos', 'Comunicação', 'Cordialidade', 'Custo']
    for c in crit_colunas: df[c] = pd.to_numeric(df[c], errors='coerce')

    # Cálculos
    total_resp = len(df)
    nps_medio = df['nps_nota'].mean()
    media_operacional = df[crit_colunas].mean().mean()

    # Cards Superiores
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total de Respostas", total_resp)
    with c2: st.metric("NPS Médio", f"{nps_medio:.1f}" if not pd.isna(nps_medio) else "0.0")
    with c3: st.metric("Média Operacional", f"{media_operacional:.1f}" if not pd.isna(media_operacional) else "0.0")

    # --- INDICADORES (Gráficos de Rosca) ---
    st.markdown("### 🎯 Desempenho por Indicador")
    cols = st.columns(5)
    
    for i, crit in enumerate(crit_colunas):
        nota = df[crit].mean()
        nota_exibicao = nota if not pd.isna(nota) else 0.0
        with cols[i]:
            fig = go.Figure(go.Pie(
                values=[nota_exibicao, 10 - nota_exibicao if nota_exibicao <= 10 else 0],
                hole=.7,
                marker_colors=['#1f3b5c', '#eeeeee'],
                textinfo='none', showlegend=False
            ))
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=140, 
                              annotations=[dict(text=f'{nota_exibicao:.1f}', x=0.5, y=0.5, font_size=18, showarrow=False)])
            st.write(f"<p style='text-align:center; font-size:14px;'><b>{crit}</b></p>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"grafico_{crit}")

    # --- MÉDIAS POR DEPARTAMENTO ---
    st.divider()
    st.markdown("### 🏢 Médias por Departamento")
    colunas_setores = [f"Nota_{s}" for s in setores_lista]
    for c in colunas_setores: dados_brutos[c] = pd.to_numeric(dados_brutos[c], errors='coerce')
    
    medias_setores = dados_brutos[colunas_setores].mean()
    medias_setores.index = setores_lista
    st.bar_chart(medias_setores, color="#1f3b5c")

    # --- TABELA ---
    st.divider()
    st.markdown("### 💬 Últimos Feedbacks")
    st.dataframe(df[['timestamp', 'nome', 'nps_nota', 'nps_motivo']].tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erro no Dashboard: {e}")
