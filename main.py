import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from database import lista_vendedores, cliente, vendas, id_vendedor, id_cliente
import os
import mysql.connector

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered= True)

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'], icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                          orientation='horizontal')

chars = "'),([]"
if escolha == 'Reservar':
    lista = str(lista_vendedores()).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    nome_cliente = st.text_input('Nome do Cliente :').replace(' ', '_')
    cpf = st.text_input('Cpf do cliente', help='Apenas numeros')
    telefone_cliente = st.text_input('Telefone do Cliente :')
    comissario = st.selectbox('Vendedor :', lista, placeholder=' ')
    tipo = st.selectbox('Modalidade : ', ('', 'BAT', 'TUR1', 'TUR2', 'OWD', 'ADV'), placeholder='Vendedor')
    altura = st.slider('Altura do Cliente', 1.50, 2.10)
    peso = st.slider('Peso do Cliente', 40, 160)
    valor_mergulho = st.text_input('Valor do Mergulho')
    sinal = st.text_input('Valor do Sinal')
    recebedor_sinal = st.selectbox('Quem recebeu o sinal?', ['', 'AcquaWorld', 'Vendedor'])
    if recebedor_sinal == 'AcquaWorld':
        pago_loja = sinal
        pago_vendedor = 0

    if recebedor_sinal == 'Vendedor':
        pago_loja = 0
        pago_vendedor = sinal

    valor_loja = st.number_input('Receber na Loja :', format='%d', step=10)

    if st.button('Reservar'):

        cursor.execute("INSERT INTO cliente (cpf, nome, telefone, peso, altura) VALUES (%s, %s, %s, %s, %s)",
                       (cpf, nome_cliente, telefone_cliente, peso, altura))

        cursor.execute(f"SELECT id FROM vendedores WHERE nome = '{comissario}'")
        id_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

        cursor.execute(f"SELECT id FROM cliente WHERE cpf = {cpf}")
        id_cliente = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

        cursor.execute(
            "INSERT INTO vendas (data, id_cliente, id_vendedor,pago_loja, pago_vendedor) values (%s, %s, %s, %s, %s)",
            (data, id_cliente, id_vendedor, pago_loja, pago_vendedor))
        st.success('Reserva realizada com sucesso!')


