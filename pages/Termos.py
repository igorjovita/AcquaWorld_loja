import streamlit as st

from functions import select_termo_cliente, select_lista_nomes

st.subheader('Termos de responsabilidade')

if 'pesquisa_termo' not in st.session_state:
    st.session_state.pesquisa_termo = False

data_termo = st.date_input('Selecione a data para pesquisar', format='DD/MM/YYYY')
if st.button('Pesquisar'):
    st.session_state.pesquisa_termo = True

if st.session_state.pesquisa_termo:
    dados = select_termo_cliente(data_termo)
    if dados:
        st.write(f'Clientes Não Relacionados - {dados[0][1]}')
        st.write(f'Clientes Relacionados - {dados[1][1]}')
        nomes_nao_relacionados = str(dados[0][2]).split(',')
        st.selectbox('Escolha o cliente para relacionar', nomes_nao_relacionados, index=None)
        nomes_reservados, nomes_ids_reservados = select_lista_nomes(data_termo)
        select_box_reservados = st.selectbox('Clientes Reservados', nomes_reservados, index=None)

        if st.button('Relacionar'):
            id_cliente = ''
            for cliente in nomes_ids_reservados:
                if select_box_reservados == cliente[0]:
                    id_cliente = cliente[1]

            st.write(id_cliente)
