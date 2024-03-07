import streamlit as st

from functions import select_termo_cliente

st.subheader('Termos de responsabilidade')

if 'pesquisa_termo' not in st.session_state:
    st.session_state.pesquisa_termo = False

data_termo = st.date_input('Selecione a data para pesquisar', format='DD/MM/YYYY')
if st.button('Pesquisar'):
    dados = select_termo_cliente(data_termo)
    st.write(dados)


