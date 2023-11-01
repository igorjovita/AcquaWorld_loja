import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from database import lista_vendedores, cliente, vendas, id_vendedor, id_cliente

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'], icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                          orientation='horizontal')

chars = "'),([]"
if escolha == 'Reservar':
    lista = str(lista_vendedores()).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    nome = st.text_input('Nome do Cliente :').replace(' ', '_')
    cpf = st.text_input('Cpf do cliente', help='Apenas numeros')
    telefone = st.text_input('Telefone do Cliente :')
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
        cliente(cpf, nome, telefone, peso, altura)
        id_vendedor(comissario)
        id_cliente(nome)
        vendas(data, id_cliente, id_vendedor, pago_loja, pago_vendedor)
        st.success('Reserva realizada com sucesso!')
