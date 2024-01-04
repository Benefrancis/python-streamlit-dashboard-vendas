import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit.delta_generator import DeltaGenerator


# %%
def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'


# %%
## Layout da página
st.set_page_config(layout='wide')
# %%
## Cabeçalho

st.title('Dashboard de Vendas :shopping_trolley: ')
st.subheader('by Benefrancis')
DeltaGenerator()
# %%
## Requisição para a API

url = 'https://labdados.com/produtos'

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)

dados = pd.DataFrame.from_dict(response.json())

# %%
## Alterando formato da data
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

# %%
## Filtro de vendedores

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# %%
## Receita por UF
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()

receita_estados = dados.drop_duplicates(subset=['Local da compra'])[['Local da compra', 'lat', 'lon']].merge(
    receita_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)
# %%
## Receita Mensal
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()

receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month

# %%
## Receita por Categoria

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

fig_receita_estados = px.bar(receita_estados.head(), x='Local da compra', y='Preço', text_auto=True,
                             title='Top estados (receita)')

fig_receita_estados.update_layout(yaxis_title='Receita')

fig_receita_categorias = px.bar(receita_categorias, title='Receita por Categorias', text_auto=True)

fig_receita_categorias.update_layout(yaxis_title='Receita')

# %%

## Vendas por UF

vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']].merge(
    vendas_estados, left_on='Local da compra', right_index=True).sort_values('Preço', ascending=False)

vendas_mensal = pd.DataFrame(
    dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending=False))

# %%

vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

# %%
## Gráficos

### Gráfico de Receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat='lat', lon='lon',
                                  scope='south america',
                                  size='Preço',
                                  template='seaborn',
                                  hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por UF')

fig_receita_mensal = px.line(receita_mensal,
                             x='Mes',
                             y='Preço',
                             markers=True,
                             range_y=(0, receita_mensal.max()),
                             color='Ano',
                             line_dash='Ano',
                             title='Receita mensal')

fig_receita_mensal.update_layout(yaxis_title='Receita')

fig_mapa_vendas = px.scatter_geo(vendas_estados,
                                 lat='lat',
                                 lon='lon',
                                 scope='south america',
                                 # fitbounds = 'locations',
                                 template='seaborn',
                                 size='Preço',
                                 hover_name='Local da compra',
                                 hover_data={'lat': False, 'lon': False},
                                 title='Vendas por UF',
                                 )

fig_vendas_mensal = px.line(vendas_mensal,
                            x='Mes',
                            y='Preço',
                            markers=True,
                            range_y=(0, vendas_mensal.max()),
                            color='Ano',
                            line_dash='Ano',
                            title='Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_estados = px.bar(vendas_estados.head(),
                            x='Local da compra',
                            y='Preço',
                            text_auto=True,
                            title='Top 5 estados'
                            )

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

fig_vendas_categorias = px.bar(vendas_categorias,
                               text_auto=True,
                               title='Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')

# %%
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    ## Visualização da aba 1
    coluna1, coluna2 = st.columns(2)
with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    st.plotly_chart(fig_mapa_receita, use_container_width=True)
    st.plotly_chart(fig_receita_estados, use_container_width=True)

with coluna2:
    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
    st.plotly_chart(fig_receita_mensal, use_container_width=True)
    st.plotly_chart(fig_receita_categorias, use_container_width=True)
with aba2:
    ## Visualização da aba 2
    coluna1, coluna2 = st.columns(2)
with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    st.plotly_chart(fig_mapa_vendas, use_container_width=True)
    st.plotly_chart(fig_vendas_estados, use_container_width=True)

with coluna2:
    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
    st.plotly_chart(fig_vendas_mensal, use_container_width=True)
    st.plotly_chart(fig_vendas_categorias, use_container_width=True)
with aba3:
    ## Visualização da aba 3
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)

with coluna1:
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values(by='sum', ascending=False).head(qtd_vendedores),
                                    x='sum',
                                    y=vendedores[['sum']].sort_values(by='sum', ascending=False).head(
                                        qtd_vendedores).index,
                                    text_auto=True,
                                    title=f'Top {qtd_vendedores} (receita)')
    st.plotly_chart(fig_receita_vendedores, use_container_width=True)

with coluna2:
    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
    fig_venda_vendedores = px.bar(vendedores[['count']].sort_values(by='count', ascending=False).head(qtd_vendedores),
                                  x='count',
                                  y=vendedores[['count']].sort_values(by='count', ascending=False).head(
                                      qtd_vendedores).index,
                                  text_auto=True,
                                  title=f'Top {qtd_vendedores} (qtd vendas)')
    st.plotly_chart(fig_venda_vendedores, use_container_width=True)
    # %%
