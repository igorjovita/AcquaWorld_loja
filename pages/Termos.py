import base64
import streamlit as st
from functions import select_termo_cliente, select_lista_nomes, update_reserva_cliente_termo, update_termo_cliente, \
    update_info_reserva, html_termo, authenticate
import streamlit.components.v1
from streamlit_option_menu import option_menu
import yaml
from yaml.loader import SafeLoader

import streamlit_authenticator as stauth


if st.session_state["authentication_status"]:

    st.subheader('Termos de responsabilidade')

    menu_termo = option_menu(menu_title="Termo de Responsabilidade", options=['Visualizar', 'Editar'],
                             icons=['card-checklist', 'pencil-square'],
                             orientation='horizontal')

    if menu_termo == 'Editar':

        if 'pesquisa_termo' not in st.session_state:
            st.session_state.pesquisa_termo = False

        st.subheader("Relacionar Termos")
        data_termo = st.date_input('Selecione a data para pesquisar', format='DD/MM/YYYY')
        if st.button('Pesquisar'):
            st.session_state.pesquisa_termo = True

        if st.session_state.pesquisa_termo:
            dados, lista_relacionado, lista_nao_relacionado, lista_total = select_termo_cliente(data_termo)

            if dados:
                if len(lista_nao_relacionado) == 0:
                    st.success('Todos os termos estão relacionados aos clientes')
                else:

                    select_box_nao_relacionado = st.selectbox('Escolha o cliente para relacionar', lista_nao_relacionado,
                                                              index=None)
                    nomes_reservados, nomes_ids_reservados = select_lista_nomes(data_termo)
                    select_box_reservados = st.selectbox('Clientes Reservados', nomes_reservados, index=None)
                    atualizar = st.selectbox('Atualizar informaçoes do cliente?', ['Sim', 'Não'], index=None)

                    if st.button('Relacionar'):
                        tipo = ''
                        id_cliente = ''
                        for cliente in nomes_ids_reservados:
                            if select_box_reservados == cliente[0]:
                                id_cliente = cliente[1]
                                tipo = cliente[2]
                        if atualizar == 'Não':
                            st.write(id_cliente)
                            update_termo_cliente(id_cliente, select_box_nao_relacionado)

                        else:
                            update_termo_cliente(id_cliente, select_box_nao_relacionado)
                            update_reserva_cliente_termo(data_termo, id_cliente, tipo)

    if menu_termo == 'Visualizar':

        data_termo = st.date_input('Selecione a data para pesquisar', format='DD/MM/YYYY')
        dados, lista_relacionado, lista_nao_relacionado, lista_total = select_termo_cliente(data_termo)
        nome_cliente = st.selectbox('Nome cliente', lista_total, index=None)
        if st.button('Abrir Termo'):
            termo, pdf_file = html_termo(data_termo, nome_cliente)
            st.components.v1.html(termo, height=1600, width=1000)

            download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_file, "rb").read()).decode()}" download="{pdf_file}">Clique aqui para baixar</a>'
            st.markdown(download_link, unsafe_allow_html=True)

else:
    st.error('Realize o login primeiro')

