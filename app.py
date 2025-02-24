import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import pandas as pd

# Importa o webdriver_manager para gerenciar o ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager

def safe_float(value_str: str) -> float:
    """
    Converte uma string em float, removendo vírgulas, '%', etc.
    Se a conversão falhar, retorna 0.0
    """
    if not value_str:
        return 0.0
    # Remove espaços, troca ',' por '.', remove '%'
    value_str = value_str.strip().replace(',', '.').replace('%', '')
    try:
        return float(value_str)
    except ValueError:
        return 0.0

@st.cache_data(show_spinner=True, ttl=600)
def scrape_data() -> pd.DataFrame:
    # Configura as opções do Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Modo headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    # Se necessário, defina o caminho do binário do Chrome (em muitos ambientes Linux o Chromium já vem instalado)
    options.binary_location = '/usr/bin/chromium-browser'
    
    # Usa o webdriver_manager para baixar automaticamente o ChromeDriver adequado
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    url = "https://www.fundsexplorer.com.br/ranking"  
    driver.get(url)
    time.sleep(5)  

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    table_body = soup.find('tbody', class_='default-fiis-table__container__table__body skeleton-content')
    rows = table_body.find_all('tr')

    data = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 14:
            ticker_str = cells[0].get("data-value", cells[0].get_text(strip=True))
            setor_str = cells[1].get("data-value", cells[1].get_text(strip=True))
            valor_str = cells[2].get("data-value", cells[2].get_text(strip=True))
            liquidez_str = cells[3].get("data-value", cells[3].get_text(strip=True))
            pvp_str = cells[4].get("data-value", cells[4].get_text(strip=True))
            dividendo_str = cells[5].get("data-value", cells[5].get_text(strip=True))
            yield_str = cells[6].get("data-value", cells[6].get_text(strip=True))
            soma_yield_3m_str = cells[7].get("data-value", cells[7].get_text(strip=True))
            soma_yield_6m_str = cells[8].get("data-value", cells[8].get_text(strip=True))
            soma_yield_12m_str = cells[9].get("data-value", cells[9].get_text(strip=True))
            media_yield_3m_str = cells[10].get("data-value", cells[10].get_text(strip=True))
            media_yield_6m_str = cells[11].get("data-value", cells[11].get_text(strip=True))
            media_yield_12m_str = cells[12].get("data-value", cells[12].get_text(strip=True))
            soma_yield_ano_corrente_str = cells[13].get("data-value", cells[13].get_text(strip=True))
            
            # Converte cada coluna para float (ou 0.0 se não der)
            valor_float = safe_float(valor_str)
            liquidez_float = safe_float(liquidez_str)
            pvp_float = safe_float(pvp_str)
            dividendo_float = safe_float(dividendo_str)
            yield_float = safe_float(yield_str) * 12  # Anualiza o yield (simplificado)
            soma_yield_3m_float = safe_float(soma_yield_3m_str)
            soma_yield_6m_float = safe_float(soma_yield_6m_str)
            soma_yield_12m_float = safe_float(soma_yield_12m_str)
            media_yield_3m_float = safe_float(media_yield_3m_str)
            media_yield_6m_float = safe_float(media_yield_6m_str)
            media_yield_12m_float = safe_float(media_yield_12m_str)
            soma_yield_ano_corrente_float = safe_float(soma_yield_ano_corrente_str)

            # Se qualquer um desses for 0, pula a linha
            if (
                pvp_float == 0 or
                soma_yield_3m_float == 0 or
                soma_yield_6m_float == 0 or
                soma_yield_12m_float == 0 or
                media_yield_3m_float == 0 or
                media_yield_6m_float == 0 or
                media_yield_12m_float == 0
            ):
                continue

            data.append({
                'Ticker': ticker_str.strip().upper(),
                'Setor': setor_str.strip(),
                'Preço (R$)': valor_float,
                'Liquidez': liquidez_float,
                'P/VP': pvp_float,
                'Dividendo': dividendo_float,
                'Yield': yield_float,
                'Soma Yield 3M': soma_yield_3m_float,
                'Soma Yield 6M': soma_yield_6m_float,
                'Soma Yield 12M': soma_yield_12m_float,
                'Média Yield 3M': media_yield_3m_float,
                'Média Yield 6M': media_yield_6m_float,
                'Média Yield 12M': media_yield_12m_float,
                'Soma Yield Ano Corrente': soma_yield_ano_corrente_float
            })

    df = pd.DataFrame(data)

    # Ajustes de setor
    df.loc[df['Ticker'] == 'CPSH11', 'Setor'] = 'Shoppings'
    df.loc[df['Ticker'] == 'KNRI11', 'Setor'] = 'Lajes Corporativas'
    df.loc[df['Ticker'] == 'VGHF11', 'Setor'] = 'Papéis'
    df.loc[df['Ticker'] == 'ICRI11', 'Setor'] = 'Papéis'
    df.loc[df['Ticker'] == 'VGRI11', 'Setor'] = 'Imóveis Comerciais Outros'
    df.loc[df['Ticker'] == 'HGRU11', 'Setor'] = 'Imóveis Comerciais Outros'
    df.loc[df['Ticker'] == 'HGBL11', 'Setor'] = 'Logística'
    df.loc[df['Ticker'] == 'ALZR11', 'Setor'] = 'Logística'
    df.loc[df['Ticker'] == 'RZTR11', 'Setor'] = 'Terras Agrícolas'

    df['Setor'] = df['Setor'].str.title()
    df = df[~df['Setor'].str.lower().str.contains('desenvolvimento')]
    df = df[~df['Setor'].str.lower().str.contains('indefinido')]
    df = df[~df['Setor'].str.lower().str.contains('fundo-de-fundos')]
    df = df[~df['Setor'].str.lower().str.contains('agricultura')]
    df = df[~df['Setor'].str.lower().str.contains('incorporaes')]

    df['Setor'] = df['Setor'].replace({
        'Logistica': 'Logística',
        'Hibrido': 'Híbrido',
        'Lajes Corporativas': 'Lajes Corporativas',
        'Papis': 'Papéis',
        'Imves Residenciais': 'Imóveis Residenciais',
        'Agncias De Bancos': 'Agências De Bancos',
        'Servios Financeiros Diversos': 'Serviços Financeiros Diversos',
        'Imveis Industriais E Logsticos': 'Logística',
        'Imveis-Comerciais---Outros': 'Imóveis Comerciais Outros',
        'Hotis': 'Hotéis',
        'Imveis-Industriais-E-Logsticos': 'Logística',
        'Agncias-De-Bancos': 'Agências De Bancos',
        'Tecidos-Vesturio-E-Calados': 'Tecidos, Vestuário E Calçados',
        'Imveis-Residenciais': 'Imóveis Residenciais',
        'Lajes-Corporativas': 'Lajes Corporativas',
        'Servios-Financeiros-Diversos': 'Serviços Financeiros Diversos',
    })

    return df

def rank_2em1(df):
    df.sort_values(by='P/VP', ascending=True, inplace=True)
    df["Rank P/VP"] = range(1, 1 + len(df))
    df.sort_values(by='Yield', ascending=False, inplace=True)
    df["Rank DY"] = range(1, 1 + len(df))
    df["Rank 2em1"] = df["Rank P/VP"] + df["Rank DY"]
    df.sort_values(by='Rank 2em1', ascending=True, inplace=True)

def main():
    st.set_page_config(
        page_title="Método 2 em 1 para FIIs",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.markdown("""
    <style>
    .stApp {
        background-color: #1e1e1e;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Método 2 em 1 para filtro de FIIs")
    st.write("O método 2 em 1 é uma forma de filtrar FIIs baseado em dois critérios: P/VP e DY atual. O método ordena os FIIs de acordo com o P/VP e DY atual, mas não se esqueça de ler os RIs.")

    # Chama o scraping imediatamente na inicialização
    df = scrape_data()

    col1, col2 = st.columns(2)
    with col1:
        dy_min = st.number_input("Dividend Yield Mín. (%)", value=7.0)
    with col2:
        liquidez_min = st.number_input("Liquidez Mín.", value=500000.0)

    col3, col4 = st.columns(2)
    with col3:
        pvp_min = st.number_input("P/VP Mín.", value=0.80)
    with col4:
        pvp_max = st.number_input("P/VP Máx.", value=1.05)

    segmento = st.multiselect(
        label="Segmento",
        options=sorted([
            'Logística', 'Shoppings', 'Lajes Corporativas', 'Terras Agrícolas', 'Hospitais',
            'Hotéis', 'Imóveis Comerciais Outros', 'Imóveis Residenciais', 'Papéis',
            'Agências de Bancos', 'Serviços Financeiros Diversos', 'Tecidos, Vestuário e Calçados'
        ]),
        placeholder="Selecione o(s) segmento(s)",
        label_visibility="visible"
    )

    if st.button("Filtrar!"):
        rank_2em1(df)
        df_filtrado = df[
            (df['Yield'] >= dy_min) &
            (df['Liquidez'] >= liquidez_min) &
            (df['P/VP'] >= pvp_min) &
            (df['P/VP'] <= pvp_max)
        ]
        if segmento:
            df_filtrado = df_filtrado[df_filtrado['Setor'].isin(segmento)]
        st.write(df_filtrado)

if __name__ == '__main__':
    main()
