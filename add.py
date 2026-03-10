import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

# 1. CONEXÃO (Não mexer aqui)
def buscar_dados():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    df = pd.DataFrame(wks.get_all_records())
    
    # Organizar nomes das colunas por posição para não dar erro
    df.columns.values[0] = "timestamp"
    df.columns.values[1] = "nome"
    df.columns.values[2] = "empresa"
    df.columns.values[3] = "nps_nota"
    df.columns.values[4] = "nps_motivo"
    # Critérios Gerais (Cols 6 a 10)
    crit_nomes = ['Clareza', 'Prazos', 'Comunicação', 'Cordialidade', 'Custo']
    for i, nome in enumerate(crit_nomes):
        df.columns.values[5 + i] = nome
    
    # Setores (Cols 11 a 28 - Notas nas ímpares)
    setores = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
    for i, nome in enumerate(setores):
        df.columns.values[10 + (i*2)] = f"Nota_{nome}"
        
    return df

# CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="Escrita Contabilidade", layout="wide")

# ESTILO CSS (Para criar os cards brancos e bordas)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 40px; color: #1f3b5c; }
    .stMetric { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 2px 2px 5px #eeeeee; }
    </style>
    """, unsafe_allow_html=True)

try:
    df = buscar_dados()
    
    # --- SIDEBAR (Barra Lateral) ---
    with st.sidebar:
        # Coloque o link da sua logo real aqui
        st.image("https://raw.githubusercontent.com/sua-logo-aqui.png", width=150) 
        st.title("Filtros")
        setor_selecionado = st.selectbox("Filtrar por Setor", ["Todos"] + ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS'])
        st.divider()
        st.write("### Exportar Dados")
        st.button("📥 Baixar em Excel")

    # --- CABEÇALHO ---
    st.title("📊 Dashboard de Performance")
    
    # Cálculos Principais
    total_resp = len(df)
    nps_medio = pd.to_numeric(df['nps_nota'], errors='coerce').mean()
    # Média operacional (média dos 5 critérios gerais)
    crit_colunas = ['Clareza', 'Prazos', 'Comunicação', 'Cordialidade', 'Custo']
    for c in crit_colunas: df[c] = pd.to_numeric(df[c], errors='coerce')
    media_operacional = df[crit_colunas].mean().mean()

    # Cards Superiores
    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Respostas", total_resp)
    c2.metric("NPS Médio", f"{nps_medio:.1f}")
    c3.metric("Média Operacional", f"{media_operacional:.1f}")

    # --- DESEMPENHO POR INDICADOR (Gráficos de Rosca) ---
    st.markdown("### 🎯 Desempenho por Indicador")
    cols_indicadores = st.columns(5)
    
    for i, crit in enumerate(crit_colunas):
        nota = df[crit].mean()
        with cols_indicadores[i]:
            fig = go.Figure(go.Pie(
                values=[nota, 10-nota],
                labels=[crit, ""],
                hole=.7,
                marker_colors=['#1f3b5c', '#eeeeee'],
                textinfo='none',
                showlegend=False
            ))
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=150, 
                              annotations=[dict(text=f'{nota:.1f}', x=0.5, y=0.5, font_size=20, showarrow=False)])
            st.write(f"<p style='text-align:center'><b>{crit}</b></p>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- MÉDIAS POR DEPARTAMENTO (Gráfico de Barras) ---
    st.divider()
    st.markdown("### 🏢 Médias por Departamento")
    setores_nomes = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
    colunas_setores = [f"Nota_{s}" for s in setores_nomes]
    for c in colunas_setores: df[c] = pd.to_numeric(df[c], errors='coerce')
    
    medias_setores = df[colunas_setores].mean()
    medias_setores.index = setores_nomes
    
    st.bar_chart(medias_setores, color="#1f3b5c")

    # --- ÚLTIMOS FEEDBACKS (Tabela) ---
    st.divider()
    st.markdown("### 💬 Últimos Feedbacks dos Clientes")
    # Seleciona apenas algumas colunas para mostrar na tabela igual ao seu print
    tabela_df = df[['timestamp', 'nome', 'nps_nota', 'nps_motivo']].tail(10)
    st.dataframe(tabela_df, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar layout: {e}")
