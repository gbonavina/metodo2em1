import sys
import asyncio
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np
import subprocess  # Para executar comandos externos

def safe_float(value_str: str) -> float:
    if not value_str:
        return 0.0
    value_str = value_str.strip().replace(',', '.').replace('%', '')
    try:
        return float(value_str)
    except ValueError:
        return 0.0

@st.cache_data(show_spinner=True, ttl=600)
def scrape_data() -> pd.DataFrame:
    # Tenta instalar o Chromium (caso ainda não tenha sido feito)
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True, timeout=30000)
    except Exception as e:
        st.error(f"Erro ao instalar Chromium com Playwright: {e}")
    
    url = "https://www.fundsexplorer.com.br/ranking"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_selector("tbody.default-fiis-table__container__table__body.skeleton-content", timeout=60000)
        time.sleep(5)
        html = page.content()
        browser.close()

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
            
            valor_float = safe_float(valor_str)
            liquidez_float = safe_float(liquidez_str)
            pvp_float = safe_float(pvp_str)
            dividendo_float = safe_float(dividendo_str)
            yield_float = ((1 + (safe_float(yield_str)/100)) * 12 - 1)
            soma_yield_3m_float = safe_float(soma_yield_3m_str)
            soma_yield_6m_float = safe_float(soma_yield_6m_str)
            soma_yield_12m_float = safe_float(soma_yield_12m_str)
            media_yield_3m_float = safe_float(media_yield_3m_str)
            media_yield_6m_float = safe_float(media_yield_6m_str)
            media_yield_12m_float = safe_float(media_yield_12m_str)
            soma_yield_ano_corrente_float = safe_float(soma_yield_ano_corrente_str)

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

    # df.loc[df['Ticker'] == 'CPSH11', 'Setor'] = 'Shoppings'
    # df.loc[df['Ticker'] == 'KNRI11', 'Setor'] = 'Lajes Corporativas'
    # df.loc[df['Ticker'] == 'VGHF11', 'Setor'] = 'Papéis'
    # df.loc[df['Ticker'] == 'ICRI11', 'Setor'] = 'Papéis'
    # df.loc[df['Ticker'] == 'VGRI11', 'Setor'] = 'Imóveis Comerciais Outros'
    # df.loc[df['Ticker'] == 'HGRU11', 'Setor'] = 'Imóveis Comerciais Outros'
    # df.loc[df['Ticker'] == 'HGBL11', 'Setor'] = 'Logística'
    # df.loc[df['Ticker'] == 'ALZR11', 'Setor'] = 'Logística'
    # df.loc[df['Ticker'] == 'RZTR11', 'Setor'] = 'Terras Agrícolas'

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
            'Agências de Bancos', 'Serviços Financeiros Diversos', 'Tecidos, Vestuário e Calçados', 'Misto'
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
