import streamlit as st


class Cadastro:

    def __init__(self, repository_vendedores, repository_pagamentos):
        self.repository_vendedores = repository_vendedores
        self.repository_pagamentos = repository_pagamentos

    def tela_cadastro(self):
        st.header('Cadastros')
        self.cadastro_vendedores()

        st.write('---')

        self.cadastro_maquina()

    def cadastro_vendedores(self):

        st.subheader('Vendedores')

        col1, col2, col3 = st.columns(3)

        with col1:
            nome_vendedor = st.text_input('Nome Vendedor')
            neto_bat = st.text_input('Neto batismo dinheiro ou pix', value=180)
            neto_tur1 = st.text_input('Neto turismo 1 queda', value=330)

        with col2:
            telefone_vendedor = st.text_input('Telefone')
            neto_bat_cartao = st.text_input('Neto batismo cartão', value=190)
            neto_tur2 = st.text_input('Neto turismo 2 quedas', value=380)

        with col3:
            apelido_vendedor = st.text_input('Apelido Vendedor', help='Nome usado pelo sistema')
            neto_acp = st.text_input('Neto acompanhante', value=80)

        if st.button('Cadastrar vendedor'):
            self.repository_vendedores.insert_vendedores(nome_vendedor, apelido_vendedor, telefone_vendedor, neto_bat,
                                                         neto_bat_cartao, neto_acp, neto_tur1, neto_tur2)
            st.success('Vendedor cadastrado com sucesso!')

    def cadastro_maquina(self):

        st.subheader('Maquinas de cartão')

        col1, col2, col3 = st.columns(3)

        with col1:
            nome_maquina = st.text_input('Nome da maquina')
            taxa_credito_parcelado = st.text_input('Taxa credito parcelado')
        with col2:
            taxa_debito = st.text_input('Taxa debito')
            taxa_pix = st.text_input('Taxa pix')
        with col3:
            taxa_credito_vista = st.text_input('Taxa credito a vista')

        if st.button('Cadastrar maquina de cartão'):
            self.repository_pagamentos.insert_maquina_cartao(nome_maquina, taxa_debito, taxa_credito_vista,
                                                             taxa_credito_parcelado, taxa_pix)

            st.success('Maquina cadastrada com sucesso!')
