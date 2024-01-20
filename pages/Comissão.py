import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from babel.numbers import format_currency
import os
import mysql.connector
from decimal import Decimal
chars = "'),([]"
chars2 = "')([]"

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered=True)

# Inicialize o estado (session state)
state = st.session_state

# Crie um DataFrame vazio para armazenar os dados
if 'df_state' not in state:
    state.df_state = pd.DataFrame(columns=['Selecionar', 'Data', 'Nome Cliente', 'Tipo', 'Valor a Receber', 'Valor a Pagar', 'Situação'])

# Comissario, Data da reserva, Nome cliente, Tipo, Pago comissario, Pago Loja

st.subheader('Comissão')
mydb.connect()
cursor.execute("SELECT apelido FROM vendedores")
lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

comissario = st.selectbox('Selecione o parceiro', lista_vendedor)
situacao = st.selectbox('Situação do Pagamento', ['Pendente', 'Pago', 'Todos'], index=None,
                        placeholder='Selecione o status do pagamento')

filtro = st.radio('Filtrar Pesquisa', options=['Todos os resultados', 'Data Especifica'])
if 'botao_pressionado' not in st.session_state:
    st.session_state.botao_pressionado = False


def pressionar():
    st.session_state.botao_pressionado = True
    # Atualize a lista de itens selecionados com os IDs correspondentes
    st.session_state.selected_items = st.session_state.df_state[st.session_state.df_state['Selecionar']].index.tolist()

total_somado = 0
if filtro == 'Data Especifica':
    data_inicio = st.date_input('Data inicial', format='DD/MM/YYYY', value=None)
    data_final = st.date_input('Data final', format='DD/MM/YYYY', value=None)
if st.button('Pesquisar Comissão', on_click=pressionar) or st.session_state.botao_pressionado:
    if filtro == 'Data Especifica':
        cursor.execute(f"SELECT id FROM vendedores where nome = '{comissario}'")
        id_vendedor = cursor.fetchone()[0]
        cursor.execute(f""" SELECT 
            reserva.Data as Data,
            GROUP_CONCAT(DISTINCT reserva.nome_cliente SEPARATOR ' , ') as Nomes_Clientes,
            GROUP_CONCAT(DISTINCT CONCAT(cnt, ' ', reserva.tipo) SEPARATOR ' + ') as Tipo_Clientes,
            SUM(lancamento_comissao.valor_receber) as Valor_Receber,
            SUM(lancamento_comissao.valor_pagar) as Valor_Pagar,
            lancamento_comissao.situacao
        FROM 
            reserva
        JOIN 
            lancamento_comissao ON reserva.Id = lancamento_comissao.Id_reserva
        JOIN 
            vendedores ON lancamento_comissao.Id_vendedor = vendedores.Id
        LEFT JOIN (
            SELECT Id_titular, Data, COUNT(*) as cnt
            FROM reserva
            GROUP BY Id_titular, Data
        ) as cnt_reserva ON reserva.Id_titular = cnt_reserva.Id_titular AND reserva.Data = cnt_reserva.Data
        WHERE 
            reserva.Data BETWEEN '{data_inicio}' AND '{data_final}' 
            AND lancamento_comissao.Id_vendedor = {id_vendedor} AND
            lancamento_comissao.situacao = '{situacao}'
        GROUP BY reserva.Id_titular, reserva.Data, lancamento_comissao.situacao""")
        resultados = cursor.fetchall()
    else:
        cursor.execute(f"SELECT id FROM vendedores where nome = '{comissario}'")
        id_vendedor = cursor.fetchone()[0]
        cursor.execute(f""" SELECT 
                    reserva.Data as Data,
                    GROUP_CONCAT(DISTINCT reserva.nome_cliente SEPARATOR ' , ') as Nomes_Clientes,
                    GROUP_CONCAT(DISTINCT CONCAT(cnt, ' ', reserva.tipo) SEPARATOR ' + ') as Tipo_Clientes,
                    SUM(lancamento_comissao.valor_receber) as Valor_Receber,
                    SUM(lancamento_comissao.valor_pagar) as Valor_Pagar,
                    lancamento_comissao.situacao
                FROM 
                    reserva
                JOIN 
                    lancamento_comissao ON reserva.Id = lancamento_comissao.Id_reserva
                JOIN 
                    vendedores ON lancamento_comissao.Id_vendedor = vendedores.Id
                LEFT JOIN (
                    SELECT Id_titular, Data, COUNT(*) as cnt
                    FROM reserva
                    GROUP BY Id_titular, Data
                ) as cnt_reserva ON reserva.Id_titular = cnt_reserva.Id_titular AND reserva.Data = cnt_reserva.Data
                WHERE  
                    lancamento_comissao.Id_vendedor = {id_vendedor} AND
                    lancamento_comissao.situacao = '{situacao}'
                GROUP BY reserva.Id_titular, reserva.Data, lancamento_comissao.situacao""")
        resultados = cursor.fetchall()
        df = pd.DataFrame(resultados,
                          columns=['Data', 'Nome Cliente', 'Tipo', 'Valor a Receber', 'Valor a Pagar', 'Situação'])

        # Adicionar coluna de seleção e formatar valores
        df.insert(0, 'Selecionar', [False] * len(df))
        df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
        soma_pagar_direta = df['Valor a Pagar'].sum()
        soma_receber_direta = df['Valor a Receber'].sum()
        df['Valor a Receber'] = df['Valor a Receber'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
        df['Valor a Pagar'] = df['Valor a Pagar'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))

        # Armazenar o DataFrame no Session State
        state.df_state = df

        # Exibir DataFrame com st.data_editor
        state.df_state = st.data_editor(state.df_state, key="editable_df", hide_index=True)

        # Calcular totais
        total_clientes = state.df_state['Nome Cliente'].str.split(',').explode().str.strip().nunique()
        soma_clientes = state.df_state['Nome Cliente'].nunique()
        soma_receber_formatado = format_currency(float(soma_receber_direta), 'BRL', locale='pt_BR')
        soma_pagar_formatado = format_currency(float(soma_pagar_direta), 'BRL', locale='pt_BR')

        # Exibir totais abaixo do DataFrame
        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("Total de clientes:")
            st.write(f'{total_clientes}')

        with col2:
            st.write(f"{comissario} pagar :")
            st.write(f'{soma_receber_formatado}')

        with col3:
            st.write(f"{comissario} receber:")
            st.write(f' {soma_pagar_formatado}')

        if len(st.session_state.df_state.loc[st.session_state.df_state['Selecionar']]) > 0:
            # Inputs para data e forma de pagamento
            data_pagamento = st.date_input("Data do Pagamento", format='DD/MM/YYYY', key="data_pagamento")
            forma_pagamento = st.text_input("Forma de Pagamento", key="forma_pagamento")

        # Botão para lançar pagamento
            if st.button("Lançar Pagamento"):
                # Calcule a soma dos valores dos itens selecionados
                total_pagar = st.session_state.df_state.loc[st.session_state.df_state['Selecionar'], 'Valor a Pagar'].sum()
                total_receber = st.session_state.df_state.loc[
                    st.session_state.df_state['Selecionar'], 'Valor a Receber'].sum()

                total = str(total_pagar).replace('R$', '').replace(',', '.').split()
                for valor in total:
                    total_somado += float(valor)

            st.write(format_currency(float(total_somado), 'BRL', locale='pt_BR'))

            # total_pagar_str = "R$ {:.2f}".format(float(total_pagar.replace('R$ ', '').replace('.', '').replace(',', '.')))
            # total_receber_str = "R$ {:.2f}".format(float(total_receber.replace('R$ ', '').replace('.', '').replace(',', '.')))
            #
            # # Exiba os totais abaixo da tabela
            # st.write(f"Total a Pagar: {total_pagar_str}")
            # st.write(f"Total a Receber: {total_receber_str}")
    # df = pd.DataFrame(resultados,
    #                   columns=['Data', 'Nome Cliente', 'Tipo', 'Valor a Receber', 'Valor a Pagar', 'Situação'])
    #
    # df.insert(0, 'Selecionar', [False] * len(df))
    # df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
    # df['Valor a Receber'] = df['Valor a Receber'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
    # df['Valor a Pagar'] = df['Valor a Pagar'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
    #
    # edited_df = st.data_editor(df, key="editable_df", hide_index=True)
    #
    # total_clientes = df['Nome Cliente'].str.split(',').explode().str.strip().nunique()
    # soma_clientes = df['Nome Cliente'].nunique()
    # soma_receber = df['Valor a Receber'].replace('[^\d.]', '', regex=True).astype(float).sum()
    # soma_pagar = df['Valor a Pagar'].replace('[^\d.]', '', regex=True).astype(float).sum()
    #
    # # Exibir a soma abaixo da tabela
    # st.write(f"Total de clientes: {total_clientes}")
    # st.write(f"{comissario} pagar AcquaWorld: R$ {soma_receber}")
    # st.write(f"AcquaWorld pagar {comissario}: R$ {soma_pagar}")

st.write('---')

st.subheader('Acerto Comissão')
