import streamlit as st
import mysql.connector
import os
import streamlit.components.v1
from functions import gerar_html_entrada_caixa, gerar_html_total
mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")


st.header('Planilha do Caixa')

col1, col2, col3 = st.columns(3)
with col1:
    data_caixa = st.date_input('Data', format='DD/MM/YYYY')

with col2:
    lancamento = st.selectbox('Lançamento', ['ENTRADA', 'SAIDA'], index=None)

with col3:
    pass

col1, col2, col3 = st.columns(3)
html_content = None
output_text, output_text2 = gerar_html_caixa(data_caixa)
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
            html_content = file.read()

if html_content:
    st.components.v1.html(html_content, height=1000, width=1000, scrolling=True)



