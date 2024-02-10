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

with st.form('Lancamento Caixa'):
    st.header('Planilha do Caixa')
    tipo1 = ['ENTRADA', 'BAT', 'TUR', 'ACP', 'CURSO', 'PGT PARCEIRO', 'OUTROS']
    tipo2 = ['CAFÉ DA MANHÃ', 'DESPESA OPERACIONAL', 'SALARIO', 'SANGRIA', 'CONTAS']
    col1, col2, col3 = st.columns(3)
    with col1:
        data_caixa = st.date_input('Data', format='DD/MM/YYYY')
        valor = st.text_input('Valor')
    with col2:
        lancamento = st.selectbox('Lançamento', ['ENTRADA', 'SAIDA'], index=None)
        if lancamento is not None and lancamento == 'ENTRADA':
            tipo = st.selectbox('Tipo', tipo1, index=None)
        else:
            tipo = st.selectbox('Tipo', tipo2, index=None)
    with col3:
        forma_pg = st.selectbox('Forma do Pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None)
    descricao = st.text_area('Descriçao')
    if st.form_submit_button('Lançar Pagamento'):
        insert_caixa(1, data_caixa, lancamento, tipo, descricao, forma_pg, valor)
        st.success('Lançamento inserido no caixa')

col1, col2, col3 = st.columns(3)
html_content = None

with col1:
    if st.button('Abrir Total'):
        with open("planilha_caixa_total.html", "r", encoding="utf-8") as file:
            html_content = gerar_html_total(data_caixa)

with col2:
    if st.button('Abrir Entrada'):
        with open("planilha_caixa_entrada.html", "r", encoding="utf-8") as file:
            html_content = gerar_html_entrada_caixa(data_caixa)
with col3:
    if st.button('Abrir Saida'):
        with open("planilha_caixa_saida.html", "r", encoding="utf-8") as file:
            html_content = gerar_html_saida_caixa(data_caixa)

if html_content:
    st.components.v1.html(html_content, height=1000, width=1000, scrolling=True)



