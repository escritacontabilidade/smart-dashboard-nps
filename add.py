import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# 1. FUNÇÃO DE CONEXÃO (Mantenha como está)
def buscar_dados():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    return pd.DataFrame(wks.get_all_records())

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Dashboard NPS", layout="wide")

# 2. ADICIONANDO SUA LOGO
# Substitua o link abaixo pelo link direto da sua imagem ou use uma imagem padrão
st.image("https://cdn-icons-png.flaticon.com/512/3112/3112946.png", width=100) 
st.title("📊 Dashboard de Satisfação do Cliente")

# Carregar os dados
try:
    df = buscar_dados()
    
    # MÁGICA PARA EVITAR O ERRO: Vamos renomear as colunas por POSIÇÃO e não por NOME
    # Assim, não importa o que você escreveu no topo da planilha, o Python vai saber a ordem
    df.columns.values[3] = "nps_nota"      # Coluna 4 (Índice 3 no Python)
    df.columns.values[4] = "nps_motivo"    # Coluna 5 (Índice 4 no Python)
    
    # Ajustando as notas dos setores (Colunas 11 a 28, pulando as sugestões)
    setores_nomes = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
    # Mapeamos as colunas de 2 em 2 começando da 10 (Python conta do zero)
    for i, nome in enumerate(setores_nomes):
        df.columns.values[10 + (i*2)] = f"Nota_{nome}"

    # Converter para número
    df['nps_nota'] = pd.to_numeric(df['nps_nota'], errors='coerce')

    # EXIBIÇÃO DO NPS
    total = len(df)
    promotores = len(df[df['nps_nota'] >= 9])
    detratores = len(df[df['nps_nota'] <= 6])
    nps_calc = ((promotores - detratores) / total) * 100 if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("NPS Geral", f"{nps_calc:.1f}")
    col2.metric("Total de Respostas", total)
    col3.info("Zona de Qualidade: 50 a 74")

    # GRÁFICO DE SETORES
    st.divider()
    st.subheader("⭐ Médias por Setor")
    colunas_notas_setores = [f"Nota_{n}" for n in setores_nomes]
    for col in colunas_notas_setores:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    medias = df[colunas_notas_setores].mean()
    # Limpando o nome para exibir no gráfico
    medias.index = setores_nomes
    st.bar_chart(medias)

    # NUVEM DE PALAVRAS
    st.divider()
    st.subheader("💬 O que mais comentam")
    comentarios = " ".join(str(v) for v in df['nps_motivo'].dropna() if v != "")
    if comentarios:
        nuvem = WordCloud(background_color="white", width=800, height=300).generate(comentarios)
        fig, ax = plt.subplots()
        ax.imshow(nuvem, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.write("Sem comentários suficientes para gerar a nuvem.")

except Exception as e:
    st.error(f"Ops! Algo deu errado. Verifique se o nome da aba na sua planilha é 'respostas'. Erro: {e}")
