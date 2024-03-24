import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import os
import streamlit.components.v1
from functions import gerar_html_entrada_caixa, gerar_html_total, gerar_html_saida_caixa, select_caixa, \
    select_fechamento
from functions import insert_caixa
from babel.numbers import format_currency


def caixa():

    mydb = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USERNAME"),
        passwd=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        autocommit=True,
        ssl_verify_identity=False,
        ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

    if 'fechamento' not in st.session_state:
        st.session_state.fechamento = False

    tipo1 = ['ENTRADA', 'BAT', 'TUR', 'ACP', 'CURSO', 'PGT PARCEIRO', 'OUTROS']
    tipo2 = ['CAFÉ DA MANHÃ', 'DESPESA OPERACIONAL', 'SALARIO', 'SANGRIA', 'CONTAS']
    lancamento = ''

    escolha_caixa = option_menu('Controle de Caixa', ['Visualizar', 'Lançamentos'], orientation='horizontal')

    if escolha_caixa == 'Lançamentos':

        st.header('Lançamento Caixa')
        col1, col2, col3 = st.columns(3)

        with col1:
            data_caixa = st.date_input('Data', format='DD/MM/YYYY')

        with col2:
            lancamento = st.selectbox('Lançamento', ['ENTRADA', 'SAIDA', 'FECHAMENTO'], index=None)

        with col3:
            if lancamento == 'FECHAMENTO':
                dados, saldo_anterior = select_caixa(data_caixa)
                soma_dinheiro = 0
                soma_saida_dinheiro = 0
                soma_cofre = 0

                for dado in dados:
                    if dado[0] == 'ENTRADA':
                        if dado[3] == 'Dinheiro':
                            soma_dinheiro += float(dado[4])

                    if dado[0] == 'SAIDA':
                        if dado[3] == 'Dinheiro':
                            soma_saida_dinheiro += float(dado[4])
                        if dado[1] == 'Cofre':
                            soma_cofre += float(dado[4])

                saldo = (soma_dinheiro + saldo_anterior) - (soma_saida_dinheiro + soma_cofre)
                saldo_loja = format_currency(saldo, 'BRL', locale='pt_BR')
                valor = st.text_input('Valor', value=saldo_loja)

            else:
                valor = st.text_input('Valor')

        colu1, colu2 = st.columns(2)

        with colu1:
            if lancamento == 'ENTRADA':
                tipo = st.selectbox('Tipo', tipo1, index=None)
            elif lancamento == 'SAIDA':
                tipo = st.selectbox('Tipo', tipo2, index=None)
            else:
                tipo = st.selectbox('Tipo', tipo2, index=None, disabled=True)

        with colu2:

            if lancamento == 'FECHAMENTO':
                forma_pg = st.selectbox('Forma do Pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None,
                                        disabled=True)
            else:
                forma_pg = st.selectbox('Forma do Pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None)

        if lancamento == 'FECHAMENTO':
            descricao = st.text_area('Descriçao', disabled=True)
        else:
            descricao = st.text_area('Descriçao')

        if st.button('Lançar Pagamento'):

            fechamento = select_fechamento(data_caixa)

            if fechamento:
                st.error('O caixa já foi fechado, faça lançamentos no dia seguinte')

            else:

                if lancamento == 'FECHAMENTO':
                    valor = saldo
                insert_caixa(1, data_caixa, lancamento, tipo, descricao, forma_pg, valor)
                st.success('Lançamento inserido no caixa')

    if escolha_caixa == 'Visualizar':
        st.header('Planilha Caixa')
        data_caixa2 = st.date_input('Data do Caixa', format='DD/MM/YYYY')

        col1, col2, col3 = st.columns(3)
        html_content = None

        with col1:
            st.write('')
            botao1 = st.button('Abrir Total')

        with col2:
            st.write('')
            botao2 = st.button('Abrir Entrada')

        with col3:
            st.write('')
            botao3 = st.button('Abrir Saida')

        if botao1:
            with open("planilha_caixa_total.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_total(data_caixa2)

        if botao2:
            with open("planilha_caixa_entrada.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_entrada_caixa(data_caixa2)

        if botao3:
            with open("planilha_caixa_saida.html", "r", encoding="utf-8") as file:
                html_content = gerar_html_saida_caixa(data_caixa2)

        if html_content:
            st.components.v1.html(html_content, height=1000, width=1000, scrolling=True)
