import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import streamlit.components.v1
import jinja2
import pdfkit
from babel.numbers import format_currency


class Caixa:
    def __init__(self, repository_pagamentos):
        self.repository_pagamentos = repository_pagamentos

    def tela_caixa(self):
        menu_opçoes = option_menu('Controle de Caixa', ['Visualizar', 'Lançamentos'], orientation='horizontal')

        if menu_opçoes == 'Visualizar':

            st.subheader('Planilhas')

            data = st.date_input('Data do caixa', format='DD/MM/YYYY')

            if st.button('Abrir Total'):
                self.planilha_caixa_entrada_saida(data, 'ENTRADA')
                st.write('---')

                self.planilha_caixa_entrada_saida(data, 'SAIDA')
                st.write('---')
                self.planilha_caixa_total(data)

        elif menu_opçoes == 'Lançamentos':

            if 'fechar_caixa' not in st.session_state:
                st.session_state.fechar_caixa = False

            st.header('Lançamento Caixa')
            col1, col2, col3 = st.columns(3)

            with col1:
                data_lancamento = st.date_input('Data', format='DD/MM/YYYY')

            with col2:
                lancamento = st.selectbox('Lançamento', ['ENTRADA', 'SAIDA'], index=None)

            with col3:
                valor = st.text_input('Valor')

            colu1, colu2 = st.columns(2)

            with colu1:

                lista_tipo = ['ENTRADA', 'BAT', 'TUR', 'ACP', 'CURSO', 'PGT PARCEIRO', 'OUTROS']
                if lancamento == 'SAIDA':
                    lista_tipo = ['CAFÉ DA MANHÃ', 'DESPESA OPERACIONAL', 'SALARIO', 'SANGRIA', 'CONTAS']

                tipo = st.selectbox('Tipo', lista_tipo, index=None)

            with colu2:
                forma_pg = st.selectbox('Forma do Pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None)

            descricao = st.text_area('Descriçao')

            coluna1, coluna2 = st.columns(2)

            with coluna1:
                if st.button('Lançar pagamento'):
                    self.repository_pagamentos.insert_caixa(1, data_lancamento, lancamento, tipo, descricao, forma_pg,
                                                            valor)

            with coluna2:
                if st.button('Fechar caixa'):
                    st.session_state.fechar_caixa = True

            if st.session_state.fechar_caixa:
                valor = st.text_input('Insira o valor do saldo do caixa')

                if st.button('Lançar fechamento'):
                    select_somatorio = self.repository_pagamentos.obter_somatorio_caixa(data_lancamento)
                    select_somatorio = select_somatorio[0]
                    saldo_loja = (
                            float(select_somatorio[8]) + float(select_somatorio[10]) - (float(select_somatorio[9])))

                    if saldo_loja == float(valor):
                        self.repository_pagamentos.insert_caixa('', data_lancamento, 'FECHAMENTO', '', '', '', valor)

                    else:
                        st.error('O valor informado está incorreto')
                    st.session_state.fechar_caixa = False

    def planilha_caixa_total(self, data):

        select_somatorio = self.repository_pagamentos.obter_somatorio_caixa(data)

        select_somatorio = select_somatorio[0]

        entrada_pix = format_currency(float(select_somatorio[0]), 'BRL', locale='pt_BR')
        entrada_dinheiro = format_currency(float(select_somatorio[1]), 'BRL', locale='pt_BR')
        entrada_debito = format_currency(float(select_somatorio[2]), 'BRL', locale='pt_BR')
        entrada_credito = format_currency(float(select_somatorio[3]), 'BRL', locale='pt_BR')
        saida_pix = format_currency(float(select_somatorio[4]), 'BRL', locale='pt_BR')
        saida_dinheiro = format_currency(float(select_somatorio[5]), 'BRL', locale='pt_BR')
        saida_cofre = format_currency(float(select_somatorio[6]), 'BRL', locale='pt_BR')
        saida_reembolso = format_currency(float(select_somatorio[7]), 'BRL', locale='pt_BR')
        total_entrada = format_currency(float(select_somatorio[8]), 'BRL', locale='pt_BR')
        total_saida = format_currency(float(select_somatorio[9]), 'BRL', locale='pt_BR')
        saldo_anterior = format_currency(float(float(select_somatorio[10])), 'BRL', locale='pt_BR')

        saldo_loja = (float(select_somatorio[8]) + float(select_somatorio[10]) - (float(select_somatorio[9])))

        coluna1, coluna2 = st.columns(2)

        with coluna1:
            st.subheader('Total de entradas')

        with coluna2:
            st.subheader('Total de saidas')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.text('Entrada Pix')
            st.text('Entrada Dinheiro')
            st.text(' Entrada Debito')
            st.text('Entrada Credito')
            st.text('Total Entrada')
            st.markdown(f"<h5>Saldo Anterior</h5>", unsafe_allow_html=True)

        with col2:
            st.text(entrada_pix)
            st.text(entrada_dinheiro)
            st.text(entrada_debito)
            st.text(entrada_credito)
            st.text(total_entrada)
            st.markdown(f"<h5>{saldo_anterior}</h5>", unsafe_allow_html=True)

        with col3:
            st.text('Saida Pix')
            st.text('Saida Dinheiro')
            st.text('Saida Cofre')
            st.text('Saida Reembolso')
            st.text('Total Saida')

            st.markdown("<h5 style='color:green'>Saldo Atual</h5>", unsafe_allow_html=True)

        with col4:
            st.text(saida_pix)
            st.text(saida_dinheiro)
            st.text(saida_cofre)
            st.text(saida_reembolso)
            st.text(total_saida)

            st.markdown(f"<h5 style='color:green'>{format_currency(saldo_loja, 'BRL', locale='pt_BR')}</h5>",
                        unsafe_allow_html=True)

    def planilha_caixa_entrada_saida(self, data, tipo_movimento):
        select = self.repository_pagamentos.obter_lancamentos_caixa(data, tipo_movimento)
        if select:
            df = pd.DataFrame(select, columns=['Tipo', 'Descriçao', 'Pagamento', 'Valor Pago'])
            st.header(f'{tipo_movimento}')
            st.markdown(df.style.hide(axis="index").to_html(), unsafe_allow_html=True)
