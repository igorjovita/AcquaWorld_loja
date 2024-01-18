import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from babel.numbers import format_currency
import os
import mysql.connector

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

        # Adicione uma coluna 'Selecionar' ao DataFrame
        df.insert(0, 'Selecionar', [False] * len(df))

        # Converta a coluna 'Data' para o formato desejado
        df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))

        # Formate as colunas 'Valor a Receber' e 'Valor a Pagar'
        df['Valor a Receber'] = df['Valor a Receber'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
        df['Valor a Pagar'] = df['Valor a Pagar'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))

        # Adicione os dados ao DataFrame de estado
        state.df_state = df

        # Exiba o DataFrame no streamlit
        st.dataframe(state.df_state)

        # Adicionando lógica para verificar se algum checkbox foi marcado
        if st.button('Lançar Pagamento'):
            # Obtenha os índices das linhas selecionadas
            linhas_selecionadas = state.df_state[state.df_state['Selecionar']].index

            # Se houver linhas selecionadas
            if not linhas_selecionadas.empty:
                # Inicialize variáveis para acumular valores
                total_receber = 0
                total_pagar = 0

                # Crie um DataFrame temporário para armazenar os dados selecionados
                df_selecionado = state.df_state.loc[linhas_selecionadas].copy()

                # Calcule os totais a receber e a pagar
                total_receber = df_selecionado['Valor a Receber'].replace('[^\d.]', '', regex=True).astype(float).sum()
                total_pagar = df_selecionado['Valor a Pagar'].replace('[^\d.]', '', regex=True).astype(float).sum()

                # Exibir os totais abaixo do DataFrame
                st.write(f"Total a Receber: {format_currency(total_receber, 'BRL', locale='pt_BR')}")
                st.write(f"Total a Pagar: {format_currency(total_pagar, 'BRL', locale='pt_BR')}")

                # Adicione inputs para a data e a forma de pagamento
                data_pagamento = st.date_input('Data do Pagamento', format='DD/MM/YYYY', value=None)
                forma_pagamento = st.text_input('Forma de Pagamento', '')

                # Adicione um botão para lançar o pagamento
                if st.button('Confirmar Pagamento'):
                    # Itere sobre as linhas selecionadas e faça o processamento para cada uma delas
                    for indice in linhas_selecionadas:
                        # Obtenha os dados da linha
                        data = state.df_state.loc[indice, 'Data']
                        nome_cliente = state.df_state.loc[indice, 'Nome Cliente']
                        valor_receber = state.df_state.loc[indice, 'Valor a Receber']
                        valor_pagar = state.df_state.loc[indice, 'Valor a Pagar']

                        # Atualize a tabela lancamento_comissao (substitua isso pela sua lógica real)
                        cursor.execute(
                            f"UPDATE lancamento_comissao SET situacao = 'Pago' WHERE Data = '{data}' AND Nome_Cliente = '{nome_cliente}'")

                        # Insira na tabela pagamento_comissao (substitua isso pela sua lógica real)
                        cursor.execute(
                            f"INSERT INTO pagamento_comissao (Data, Nome_Cliente, Valor_Receber, Valor_Pagar, Data_Pagamento, Forma_Pagamento) VALUES ('{data}', '{nome_cliente}', {valor_receber}, {valor_pagar}, '{data_pagamento}', '{forma_pagamento}')")
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
