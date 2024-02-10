import streamlit as st
import mysql.connector
import os
import streamlit.components.v1
from functions import gerar_html_entrada_caixa, gerar_html_total, gerar_html_saida_caixa
from functions import insert_caixa


mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

tipo1 = ['ENTRADA', 'BAT', 'TUR', 'ACP', 'CURSO', 'PGT PARCEIRO', 'OUTROS']
tipo2 = ['CAFÉ DA MANHÃ', 'DESPESA OPERACIONAL', 'SALARIO', 'SANGRIA', 'CONTAS']


st.header('Lançamento Caixa')
col1, col2, col3 = st.columns(3)
with col1:
    data_caixa = st.date_input('Data', format='DD/MM/YYYY')
    valor = st.text_input('Valor')
with col2:
    lancamento = st.selectbox('Lançamento', ['ENTRADA', 'SAIDA'], index=None)
    forma_pg = st.selectbox('Forma do Pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None)

with col3:
    if lancamento == 'ENTRADA':
        tipo = st.selectbox('Tipo', tipo1, index=None)
    else:
        tipo = st.selectbox('Tipo', tipo2, index=None)

descricao = st.text_area('Descriçao')
if st.button('Lançar Pagamento'):
    insert_caixa(1, data_caixa, lancamento, tipo, descricao, forma_pg, valor)
    st.success('Lançamento inserido no caixa')

st.write('---')

st.header('Planilha Caixa')
if 'boolean1' not in st.session_state:
    st.session_state.boolean1 = False

if 'boolean2' not in st.session_state:
    st.session_state.boolean2 = False

if 'boolean3' not in st.session_state:
    st.session_state.boolean3 = False
col1, col2, col3 = st.columns(3)
html_content = None

with col1:
    st.write('')
    if st.button('Abrir Total'):
        st.session_state.boolean1 = not st.session_state.boolean1
        if st.session_state.boolean1:
            with open("planilha_caixa_total.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_total(data_caixa)

with col2:
    st.write('')
    if st.button('Abrir Entrada'):
        st.session_state.boolean2 = not st.session_state.boolean2
        if st.session_state.boolean2:
            with open("planilha_caixa_entrada.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_entrada_caixa(data_caixa)
with col3:
    st.write('')

    if st.button('Abrir Saida'):
        st.session_state.boolean3 = not st.session_state.boolean3
        if st.session_state.boolean3:
            with open("planilha_caixa_saida.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_saida_caixa(data_caixa)

if html_content:
    st.components.v1.html(html_content, height=1000, width=1000, scrolling=True)



