import streamlit as st

from functions import select_termo_cliente

st.subheader('Termos de responsabilidade')

if 'pesquisa_termo' not in st.session_state:
    st.session_state.pesquisa_termo = False

data_termo = st.date_input('Selecione a data para pesquisar', format='DD/MM/YYYY')
if st.button('Pesquisar'):
    dados = select_termo_cliente(data_termo)
    if dados:
        st.write(f'Clientes Relacionados - {dados[0][1]}')
        st.write(f'Clientes Não Relacionados - {dados[1][1]}')
        nomes_nao_relacionados = str(dados[1][2]).split(',')
        st.selectbox('Escolha o cliente para relacionar',nomes_nao_relacionados, index=None )
    st.write(dados)


