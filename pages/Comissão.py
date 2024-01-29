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

total_pagar_somado = 0
total_receber_somado = 0
if filtro == 'Data Especifica':
    data_inicio = st.date_input('Data inicial', format='DD/MM/YYYY', value=None)
    data_final = st.date_input('Data final', format='DD/MM/YYYY', value=None)
if st.button('Pesquisar Comissão', on_click=pressionar) or st.session_state.botao_pressionado:
    if filtro == 'Data Especifica':
        cursor.execute(f"SELECT id FROM vendedores where nome = '{comissario}'")
        id_vendedor = cursor.fetchone()[0]
        cursor.execute(f""" SELECT 
            reserva.Data as Data,
            reserva.nome_cliente as Nome_Titular,
            GROUP_CONCAT(DISTINCT CONCAT(cnt, ' ', reserva.tipo) SEPARATOR ' + ') as Tipos_Reserva,
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
                        reserva.nome_cliente as Nome_Titular,
                        GROUP_CONCAT(DISTINCT CONCAT(cnt, ' ', reserva.tipo) SEPARATOR ' + ') as Tipos_Reserva,
                        SUM(lancamento_comissao.valor_receber) as Valor_Receber,
                        SUM(lancamento_comissao.valor_pagar) as Valor_Pagar,
                        COALESCE(SUM(pagamentos_soma.pagamento), 0) as Valor_Pago,
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
                    LEFT JOIN (
                        SELECT id_reserva, SUM(pagamento) as pagamento
                        FROM pagamentos
                        WHERE recebedor = 'AcquaWorld'
                        GROUP BY id_reserva
                    ) as pagamentos_soma ON reserva.Id = pagamentos_soma.id_reserva
                    WHERE  
                        lancamento_comissao.Id_vendedor = {id_vendedor} AND
                        lancamento_comissao.situacao = '{situacao}'
                    GROUP BY reserva.Id_titular, reserva.Data, lancamento_comissao.situacao;

                    """)
        resultados = cursor.fetchall()
        df = pd.DataFrame(resultados,
                          columns=['Data', 'Nome Titular', 'Tipo', 'Valor a Receber', 'Valor a Pagar', 'Pago Loja', 'Situação'])

        # Adicionar coluna de seleção e formatar valores
        df.insert(0, 'Selecionar', [False] * len(df))
        df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
        soma_pagar_direta = df['Valor a Pagar'].sum()
        soma_receber_direta = df['Valor a Receber'].sum()
        df['Valor a Receber'] = df['Valor a Receber'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
        df['Valor a Pagar'] = df['Valor a Pagar'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
        df['Pago Loja'] = df['Pago Loja'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))

        # Armazenar o DataFrame no Session State
        state.df_state = df

        # Exibir DataFrame com st.data_editor
        state.df_state = st.data_editor(state.df_state, key="editable_df", hide_index=True)

        # Calcular totais

        soma_receber_formatado = format_currency(float(soma_receber_direta), 'BRL', locale='pt_BR')
        soma_pagar_formatado = format_currency(float(soma_pagar_direta), 'BRL', locale='pt_BR')

        # Exibir totais abaixo do DataFrame
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"{comissario} pagar :")
            st.write(f'{soma_receber_formatado}')

        with col2:
            st.write(f"{comissario} receber:")
            st.write(f' {soma_pagar_formatado}')

        if len(st.session_state.df_state.loc[st.session_state.df_state['Selecionar']]) > 0:
            st.write('---')
            st.subheader('Acerto Comissão')
            # Calcule a soma dos valores dos itens selecionados
            total_pagar = st.session_state.df_state.loc[st.session_state.df_state['Selecionar'], 'Valor a Pagar'].sum()
            total_receber = st.session_state.df_state.loc[
                st.session_state.df_state['Selecionar'], 'Valor a Receber'].sum()

            lista_titular = st.session_state.df_state.loc[
                st.session_state.df_state['Selecionar'], 'Nome Titular'].tolist()

            total = str(total_pagar).replace('R$', '').replace('.', '').replace(',', '.').split()
            for valor in total:
                total_pagar_somado += float(valor)

            total2 = str(total_receber).replace('R$', '').replace(',', '.').split()
            for valor2 in total2:
                total_receber_somado += float(valor2)

            if total_pagar_somado > total_receber_somado:
                pagamento = float(total_pagar_somado) - float(total_receber_somado)
                recebedor = f'{comissario} receber :'
            else:
                pagamento = float(total_receber_somado) - float(total_pagar_somado)
                recebedor = f'{comissario} pagar :'

            pagamento_input = st.text_input(label=recebedor, value=pagamento)
            data_pagamento = st.date_input("Data do Pagamento", format='DD/MM/YYYY', key="data_pagamento")
            forma_pagamento = st.selectbox("Forma de Pagamento", options=['Pix', 'Dinheiro'], key="forma_pagamento", index=None)


        # Botão para lançar pagamento
            if st.button("Lançar Pagamento"):
                lista_ids = []

                with mydb.cursor() as cursor:
                    for titular in lista_titular:
                        cursor.execute(f"SELECT id_cliente from reserva where nome_cliente = '{titular}'")
                        id_titular = cursor.fetchone()[0]
                        st.write(id_titular)

                        cursor.execute(f"SELECT id from lancamento_comissao where id_titular = {id_titular}")
                        id_comissao = [result[0] for result in cursor.fetchall()]
                        lista_ids.extend(id_comissao)

                    # Recuperar os resultados da segunda consulta antes de fechar o cursor

                    st.write(lista_ids)


                    # Fora do loop for, você pode executar operações adicionais com um novo cursor
                    for numero in lista_ids:
                        if recebedor == f'{comissario} receber':
                            pagador = 'AcquaWorld'
                        else:
                            pagador = f'{comissario}'

                        cursor.execute(f"SELECT valor_pagar from lancamento_comissao where id = {numero}")
                        valor_pagar = cursor.fetchone()[0]
                        cursor.execute(
                            "INSERT INTO pagamento_comissao (id_comissao, data, pagador, valor) VALUES (%s, %s, %s, %s)",
                            (numero, data_pagamento, pagador, valor_pagar))
                #
                # st.write(lista_titular)





