import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from database import lista_vendedores

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'], icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                          orientation='horizontal')

chars = "'),([]"
if escolha == 'Reservar':
    lista = str(lista_vendedores()).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    nome = st.text_input('Nome do Cliente :').replace(' ', '_')
    telefone = st.text_input('Telefone do Cliente :')
    comissario = st.selectbox('Vendedor :', lista, placeholder=' ')
    tipo = st.selectbox('Modalidade : ', ('', 'BAT', 'TUR1', 'TUR2', 'OWD', 'ADV'), placeholder='Vendedor')
    altura = st.slider('Altura do Cliente', 1.50, 2.10)
    peso = st.slider('Peso do Cliente', 40, 160)
    sinal = st.text_input('Valor do Sinal')
    recebedor_sinal = st.selectbox('Quem recebeu o sinal?', ['', 'AcquaWorld', 'Vendedor'])
    valor_loja = st.number_input('Receber na Loja :', format='%d', step=10)

