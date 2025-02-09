import os
import yfinance as yf
import pymysql
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DECIMAL, DATETIME
from sqlalchemy.exc import IntegrityError

agora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def baixar_dados_AC():
    # Busca no site fundamentus

    url = 'https://www.fundamentus.com.br/resultado.php'

    agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}

    resposta = requests.get(url, headers=agent)

    soup = BeautifulSoup(resposta.text, 'lxml')

    tabela = soup.find_all('table')[0]

    df = pd.read_html(str(tabela), decimal=',', thousands='.')[0]

    # Lista de colunas de Ações com %
    colunas = ['Div.Yield', 'ROIC', 'Mrg Ebit', 'Mrg. Líq.', 'ROE', 'Cresc. Rec.5a']

    # Loop for para processar cada coluna
    for coluna in colunas:
        df[coluna] = df[coluna].str.replace("%", "", regex=False)
        df[coluna] = df[coluna].str.replace(".", "", regex=False)
        df[coluna] = df[coluna].str.replace(",", ".", regex=False)
        df[coluna] = df[coluna].astype(float)

    df['ROE'] = df['ROE'].round(2)

    #funds_acoes['Papel'] = funds_acoes.index
    #df.insert(0,'Papel',df.index)
    df.insert(0,'update',agora)
    df = df.reset_index(drop=True)
    print(df)

    return df

def baixar_dados_FII():
    # Busca no site fundamentus

    urlfii = 'https://www.fundamentus.com.br/fii_resultado.php'

    agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}

    respostafii = requests.get(urlfii, headers=agent)

    soupfii = BeautifulSoup(respostafii.text, 'lxml')

    tabelafii = soupfii.find_all('table')[0]

    dfii = pd.read_html(str(tabelafii), decimal=',', thousands='.')[0]

    # Lista de colunas de Fiis com %
    colunasf = ['Dividend Yield', 'FFO Yield', 'Vacância Média', 'Cap Rate']

    # Loop for para processar cada coluna
    for coluna in colunasf:
        dfii[coluna] = dfii[coluna].str.replace("%", "", regex=False)
        dfii[coluna] = dfii[coluna].str.replace(".", "", regex=False)
        dfii[coluna] = dfii[coluna].str.replace(",", ".", regex=False)
        dfii[coluna] = dfii[coluna].astype(float)
    


    return dfii

def formula_fii(dfii):
    # Rodar essa parte apenas em datas específicas

    # Filtros no data frame de Fii

    Vaq = dfii[(dfii['Cotação'] <= 200) & (dfii['Liquidez'] >= 500000) & (dfii['Vacância Média'] <= 15) & (dfii['Dividend Yield'] > 6) & (dfii['Dividend Yield'] < 16)]

    # Aplicação da fórmula de Fii Hibrid

    FiiT = Vaq[Vaq['Qtd de imóveis'] >= 0]

    Opvp = FiiT.sort_values(by='P/VP', ascending=True)
    Opvp = Opvp.reset_index(drop=True)
    Opvp['Ordem P/VP'] = Opvp.index

    Offo = Opvp.sort_values(by='Dividend Yield', ascending=False)
    Offo = Offo.reset_index(drop=True)
    Offo['Ordem Dividend Yield'] = Offo.index

    Offo['Score'] = Offo['Ordem P/VP'] + Offo['Ordem Dividend Yield']
    FiiT = Offo.sort_values(by='Score', ascending=True)

    FiiT.reset_index(inplace=True)
    FiiT.drop('index', axis=1, inplace=True)

    return FiiT

def hist_dividendos_3anos_fii_novo(Ac):
    # Histórico de dividendos das ações
    tickers = Ac.loc[:, 'Papel'] + ".SA"

    dividendos_totais = []
    anos = ['2023', '2022']

    # Inicializa as colunas para cada ano no DataFrame
    for ano in anos:
        Ac[f'Div. {ano}'] = 0.0

    for ticker in tickers:
        div6 = []

        try:
            div = yf.Ticker(ticker).dividends
            time.sleep(0.5)

            # Verifica se o índice é do tipo datetime
            if not isinstance(div.index, pd.DatetimeIndex):
                div.index = pd.to_datetime(div.index)

        except Exception as e:
            # Em caso de erro, continue com o próximo ticker
            y = 0
            dividendos_totais.append(y)

        else:
            # Para cada ano, calcula e insere os dividendos no DataFrame
            for ano in anos:
                if ano in div.index.year.astype(str):
                    total_div = div[div.index.year == int(ano)].sum()
                    div6.append(total_div)
                    Ac.loc[Ac['Papel'] + ".SA" == ticker, f'Div. {ano}'] = total_div
                else:
                    div6.append(0)
                    Ac.loc[Ac['Papel'] + ".SA" == ticker, f'Div. {ano}'] = 0.0

            y = sum(div6)
            dividendos_totais.append(y)

    t_anos = len(anos)
    # Calcula o total de dividendos dos últimos 2 anos
    Ac['Div. 2A'] = dividendos_totais

    # Calcula a coluna PJ (presumivelmente relacionado ao preço justo)
    Ac['PJ'] = (Ac['Div. 2A'] / t_anos) / 0.08

    return Ac

def formula_magica_ROE(df):
    # Filtros no data frame de Ações e aplicação da estratégia

    filtros = df[(df['Cotação'] <= 100) &
               (df['Liq.2meses'] >= 1000000) &
               (df['Dív.Brut/ Patrim.'] >= 0) &
               (df['Dív.Brut/ Patrim.'] <= 4) &
               (df['ROE'] >= 0.10) &
               (df['P/L'] > 0) &
               (df['P/L'] < 15)&
               ~(df['Papel'].isin(['PETR4', 'PETR3', 'VALE3']))]

    # Aplicação da fórmula nas ações
    df['ROE'] = df['ROE'].round(2)

    Olp = filtros.sort_values(by='P/L', ascending=True)
    Olp = Olp.reset_index(drop=True)
    Olp['Ordem P/L'] = Olp.index

    Oroe = Olp.sort_values(by='ROE', ascending=False)
    Oroe = Oroe.reset_index(drop=True)
    Oroe['Ordem ROE'] = Oroe.index
    dados = Oroe

    dados['Score'] = dados['Ordem P/L'] + dados['Ordem ROE']
    dados = dados.sort_values(by='Score', ascending=True)

    # Remove os Tickers duplicados
    dados['PapelF'] = dados['Papel'].str[:4]
    Ac = dados.drop_duplicates(subset='PapelF')

    Ac.reset_index(inplace=True)
    Ac = Ac.drop('index', axis=1)

    print(Ac)
    
    return Ac

def Acoes_analise(Ac):
    # Histórico de dividendos das ações
    tickers = Ac['Papel'] + ".SA"

    infos = []

    for ticker in tickers:
        try:
            ticker_data = yf.Ticker(ticker)
            time.sleep(0.4)
            info = ticker_data.info
            print(f"{ticker} ok")
            
            # Normalizando o dicionário JSON para DataFrame
            info_normalized = pd.json_normalize(info)
            info_normalized['ticker'] = ticker  # Adiciona o ticker para referência
        except Exception as e:
            # Handle error and append default values
            info_normalized = pd.DataFrame([{"error": str(e), "ticker": ticker}])

        infos.append(info_normalized)

    # Concatenando todos os DataFrames em um único DataFrame
    infos_df = pd.concat(infos, ignore_index=True)

    # Unindo as informações ao DataFrame original 'Ac' pelo índice
    Ac = pd.concat([Ac.reset_index(drop=True), infos_df.reset_index(drop=True)], axis=1)

    Ac = Ac[~(Ac['sector'].isin(['Consumer Cyclical', 'Heslthcare',  'Real Estate', 'Thechnology'])) &
            ~(Ac['industry'].isin(['Residencial Construction', 'Steel', 'Household & Personal Products']))]
    return Ac

def hist_dividendos_5anos(Ac):
    # Histórico de dividendos das ações
    tickers = Ac['Papel'] + ".SA"

    dividendos = []
    #segmento = []
    #setor = []
    #nome_c = []

    for ticker in tickers:
        try:
            ticker_data = yf.Ticker(ticker)
            div = ticker_data.dividends
            time.sleep(0.5)
            #setr = ticker_data.info.get('sector', 'N/A')
            #time.sleep(0.3)
            #seg = ticker_data.info.get('industry', 'N/A')
            #time.sleep(0.3)
            #nc = ticker_data.info.get('shortName', 'N/A')
            #time.sleep(0.3)

            # Lista para os dividendos dos últimos 5 anos
            anos = ['2023', '2022', '2021']
            div6 = [div.get(x, 0).sum() for x in anos]
            y = sum(div6)

        except Exception as e:
            # Handle error and append default values
            y, setr, seg, nc = 0, 'N/A', 'N/A', 'N/A'

        dividendos.append(y)
        #setor.append(setr)
        #segmento.append(seg)
        #nome_c.append(nc)

    Ac['Div. 3A'] = dividendos
    Ac['PJ'] = (Ac['Div. 3A'] / 3) / 0.06
    #Ac['Setor'] = setor
    #Ac['Seg'] = segmento
    #Ac['Nome Curto'] = nome_c

    Ac = Ac[['update', 'Papel', 'Cotação', 'P/L','Div.Yield','Mrg. Líq.', 'ROIC', 'ROE', 'Ordem P/L', 'Ordem ROE', 'Score','Div. 3A','PJ']]
    
    return Ac

def db_criar():

    #db_user = os.getenv("DB_USER")
    #db_senha = os.getenv("DB_SENHA")
    #db_host = os.getenv("DB_HOST")
    #db_name = os.getenv("DB_NAME")

    # string de conexão com o banco de dados, passando as variáveis do .env
    #engine = create_engine(f'mysql+pymysql://{db_user}:{db_senha}@{db_host}/{db_name}')

    engine = create_engine('mysql+pymysql://root:199856@localhost/db_assinv')

    # Instanciando o objeto MetaData para criar a tabela no banco de dados
    metadata = MetaData()

    # Cria a tabela 'funds_acoes' com todas as colunas necessárias
    funds_acoes = Table('funds_acoes', metadata,
        Column('id', Integer, primary_key=True),
        Column('update', DATETIME),
        Column('Papel', String(10)),
        Column('Cotação', DECIMAL(10, 2)),
        Column('P/L', DECIMAL(10, 2)),
        Column('P/VP', DECIMAL(10, 2)),
        Column('PSR', DECIMAL(10, 2)),
        Column('Div.Yield', DECIMAL(10, 5)),
        Column('P/Ativo', DECIMAL(10, 2)),
        Column('P/Cap.Giro', DECIMAL(10, 2)),
        Column('P/EBIT', DECIMAL(10, 2)),
        Column('P/Ativ Circ.Liq', DECIMAL(10, 2)),
        Column('EV/EBIT', DECIMAL(10, 2)),
        Column('EV/EBITDA', DECIMAL(10, 2)),
        Column('Mrg Ebit', DECIMAL(10, 2)),
        Column('Mrg. Líq.', DECIMAL(10, 2)),
        Column('Liq. Corr.', DECIMAL(10, 2)),
        Column('ROIC', DECIMAL(10, 5)),
        Column('ROE', DECIMAL(10, 5)),
        Column('Liq.2meses', DECIMAL(16, 2)),
        Column('Patrim. Líq', DECIMAL(16, 2)),
        Column('Dív.Brut/ Patrim.', DECIMAL(10, 2)),
        Column('Cresc. Rec.5a', DECIMAL(10, 2))
    )

    formula_magica = Table('formula_magica', metadata,
        Column('id', Integer, primary_key=True),
        Column('update', DATETIME),  # You might want to specify the data type and default value
        Column('Papel', String(10)),
        Column('Cotação', DECIMAL(10, 2)),
        Column('P/L', DECIMAL(10, 2)),
        Column('Div.Yield', DECIMAL(10, 5)),
        Column('Mrg. Líq.', DECIMAL(10, 4)),  # Adjusted to accommodate the precision
        Column('ROIC', DECIMAL(10, 5)),
        Column('ROE', DECIMAL(10, 5)),
        Column('Ordem P/L', Integer),
        Column('Ordem ROE', Integer),
        Column('Score', Integer),
        Column('Div. 5A', DECIMAL(10, 5)),
        Column('PJ', DECIMAL(10, 4)),
        Column('Setor', String(50)),  # Adjusted to accommodate the length
        Column('Seg', String(50)),  # Adjusted to accommodate the length
        Column('Nome Curto', String(50))  # Adjusted to accommodate the length
    )

    metadata.create_all(engine)

def db_alimentar(df1,df2):
    
    df1 = df1.replace([float('inf'), float('-inf')], pd.NA)
    df2 = df2.replace([float('inf'), float('-inf')], pd.NA)

    #db_user = os.getenv("DB_USER")
    #db_senha = os.getenv("DB_SENHA")
    #db_host = os.getenv("DB_HOST")
    #db_name = os.getenv("DB_NAME")

    # string de conexão com o banco de dados, passando as variáveis do .env
    #engine = create_engine(f'mysql+pymysql://{db_user}:{db_senha}@{db_host}/{db_name}')

    engine = create_engine('mysql+pymysql://root:199856@localhost/db_assinv')

    df1.to_sql('funds_acoes', con=engine, if_exists='append', index=False)  # Converte a linha em um DataFrame de uma única linha e insere no banco de dados

    df2.to_sql('formula_magica', con=engine, if_exists='append', index=False)  # Converte a linha em um DataFrame de uma única linha e insere no banco de dados


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    
    csv1 = baixar_dados_AC()

    csv2 = Acoes_analise(formula_magica_ROE(csv1))
    csv2.to_csv("info_acoes.csv")

    csv3 = baixar_dados_FII()

    csv4 = Acoes_analise(formula_fii(csv3))
    csv4.to_csv("info_fiis.csv")

    #db_criar()
    #db_alimentar(csv1,csv2) 
