import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Função que você já validou para conectar no Google Sheets
def buscar_dados():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    sh = client.open_by_key(st.secrets["SHEET_ID"])
    wks = sh.worksheet("respostas")
    return pd.DataFrame(wks.get_all_records())

# Título do Site
st.set_page_config(page_title="Dashboard de Satisfação", layout="wide")
st.title("📊 Painel de Resultados - Pesquisa de Satisfação")

# Carregar dados
df = buscar_dados()

# Cálculo de NPS
df['Nota NPS'] = pd.to_numeric(df['Nota NPS'], errors='coerce')
total = len(df)
promotores = len(df[df['Nota NPS'] >= 9])
detratores = len(df[df['Nota NPS'] <= 6])
nps_valor = ((promotores - detractors) / total) * 100 if total > 0 else 0

# Exibir NPS em destaque
st.metric("NPS Geral", f"{nps_valor:.1f}")

# Gráfico de Setores
st.subheader("Médias por Setor")
colunas_setores = ['Contábil', 'Folha', 'Recrutamento', 'Legal', 'Financeiro', 'BPO', 'Recepção', 'Estrutura', 'CS']
medias = df[colunas_setores].apply(pd.to_numeric, errors='coerce').mean()
st.bar_chart(medias)

# Nuvem de Palavras
st.subheader("O que dizem os clientes")
texto = " ".join(str(v) for v in df['Motivo NPS'].dropna())
nuvem = WordCloud(background_color="white").generate(texto)
fig, ax = plt.subplots()
ax.imshow(nuvem)
ax.axis("off")
st.pyplot(fig)
