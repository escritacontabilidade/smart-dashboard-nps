import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import plotly.graph_objects as go

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
        
    return df

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
    df = buscar_dados()
    
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        # Tenta carregar a logo se você subiu ela no GitHub com este nome exato
        try:
            st.image("Logo Escrita.png", width=200)
        except:
            st.write("### ESCRITA CONTABILIDADE")
            
        st.title("Filtros")
        setores_lista = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
        setor_selecionado = st.selectbox("Filtrar por Setor", ["Todos"] + setores_lista)
        
        st.divider()
        st.write("### Ações")
        st.button("📥 Baixar em Excel")

    # --- TÍTULO ---
    st.markdown("# 📊 Dashboard de Performance")
    
    # Cálculos
    df['nps_nota'] = pd.to_numeric(df['nps_nota'], errors='coerce')
    total_resp = len(df)
    nps_medio = df['nps_nota'].mean()
    
    crit_colunas = ['Clareza', 'Prazos', 'Comunicação', 'Cordialidade', 'Custo']
    for c in crit_colunas: df[c] = pd.to_numeric(df[c], errors='coerce')
    media_operacional = df[crit_colunas].mean().mean()

    # Cards Superiores
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total de Respostas", total_resp)
    with c2: st.metric("NPS Médio", f"{nps_medio:.1f}")
    with c3: st.metric("Média Operacional", f"{media_operacional:.1f}")

    # --- INDICADORES (Gráficos de Rosca) ---
    st.markdown("### 🎯 Desempenho por Indicador")
    cols = st.columns(5)
    
    for i, crit in enumerate(crit_colunas):
        nota = df[crit].mean()
        with cols[i]:
            fig = go.Figure(go.Pie(
                values=[nota, 10-nota if nota <=10 else 0],
                hole=.7,
                marker_colors=['#1f3b5c', '#eeeeee'],
                textinfo='none', showlegend=False
            ))
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=140, width=140,
                              annotations=[dict(text=f'{nota:.1f}', x=0.5, y=0.5, font_size=18, showarrow=False)])
            st.write(f"<p style='text-align:center; font-size:14px;'><b>{crit}</b></p>", unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # --- MÉDIAS POR DEPARTAMENTO ---
    st.divider()
    st.markdown("### 🏢 Médias por Departamento")
    colunas_setores = [f"Nota_{s}" for s in setores_lista]
    for c in colunas_setores: df[c] = pd.to_numeric(df[c], errors='coerce')
    
    medias_setores = df[colunas_setores].mean()
    medias_setores.index = setores_lista
    st.bar_chart(medias_setores, color="#1f3b5c")

    # --- TABELA ---
    st.divider()
    st.markdown("### 💬 Últimos Feedbacks")
    st.dataframe(df[['timestamp', 'nome', 'nps_nota', 'nps_motivo']].tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Aguarde a instalação dos pacotes ou verifique o erro: {e}")
