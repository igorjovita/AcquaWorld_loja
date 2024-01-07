import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

import os
import mysql.connector
from datetime import date, datetime

chars = "'),([]"
chars2 = "')([]"

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered=True)


# Comissario, Data da reserva, Nome cliente, Tipo, Pago comissario, Pago Loja

st.subheader('Comissão')
mydb.connect()
cursor.execute("SELECT apelido FROM vendedores")
lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

comissario = st.selectbox('Selecione o parceiro', lista_vendedor)
situacao = st.selectbox('Situação do Pagamento', ['Pendente', 'Pago', 'Todos'], index=None, placeholder='Selecione o status do pagamento')
data_inicio = st.date_input('Data inicial', format='DD/MM/YYYY', value=None)
data_final = st.date_input('Data final', format='DD/MM/YYYY', value=None)
if st.button('Pesquisar Comissão'):
    cursor.execute(f"SELECT id FROM vendedores where nome = '{comissario}'")
    id_vendedor = cursor.fetchone()[0]
    cursor.execute(f"SELECT reserva.data, reserva.nome_cliente, reserva.tipo, vendedores.nome, lancamento_comissao.valor_receber, lancamento_comissao.valor_pagar, lancamento_comissao.situacao FROM reserva JOIN lancamento_comissao ON reserva.id = lancamento_comissao.id_reserva JOIN vendedores on lancamento_comissao.id_vendedor = vendedores.id WHERE reserva.data BETWEEN '{data_inicio}' and '{data_final}' and lancamento_comissao.id_vendedor = {id_vendedor}")
    resultados = cursor.fetchall()
    st.write(resultados)


