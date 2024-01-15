import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

import os
import mysql.connector
from datetime import date, datetime

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


# Comissario, Data da reserva, Nome cliente, Tipo, Pago comissario, Pago Loja

st.subheader('Comissão')
mydb.connect()
cursor.execute("SELECT apelido FROM vendedores")
lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

comissario = st.selectbox('Selecione o parceiro', lista_vendedor)
situacao = st.selectbox('Situação do Pagamento', ['Pendente', 'Pago', 'Todos'], index=None, placeholder='Selecione o status do pagamento')

filtro = st.radio('Filtrar Pesquisa',options=['Todos os resultados', 'Data Especifica'])
if filtro == 'Data Especifica':
    data_inicio = st.date_input('Data inicial', format='DD/MM/YYYY', value=None)
    data_final = st.date_input('Data final', format='DD/MM/YYYY', value=None)
if st.button('Pesquisar Comissão'):
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

    df = pd.DataFrame(resultados, columns=['Data', 'Nome Cliente', 'Tipo', 'Valor a Receber', 'Valor a Pagar', 'Situação'])
    # Criando layout de duas colunas
    col1, col2 = st.columns([0.1, 4.9])

    # Adicionando coluna com checkboxes à primeira coluna
    checkboxes = col1.checkbox(label="", key="checkbox_select_all")
    for i in range(len(df)):
        checkboxes = [col1.checkbox(label="", key=f"checkbox_{i}")]
        
    df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
    total_clientes = df['Nome Cliente'].str.split(',').explode().str.strip().nunique()
    soma_clientes = df['Nome Cliente'].nunique()
    soma_receber = df['Valor a Receber'].sum()
    soma_pagar = df['Valor a Pagar'].sum()
    df_soma = pd.DataFrame({'Data': ['Total'], 'Nome Cliente': f'{soma_clientes} clientes', 'Valor a Receber': f'R$ {soma_receber:.2f}', 'Valor a Pagar': f'R$ {soma_pagar:.2f}'})
    df_final = pd.concat([df, df_soma])
    # Remover a última linha (soma total) antes de exibir a tabela

    col2.table(df.style.format({
        'Valor Receber': 'R${:,.2f}',
        'Valor Pagar': 'R${:,.2f}'
    }).set_properties(**{'text-align': 'center'}).set_table_styles([{
        'selector': 'th',
        'props': [
            ('text-align', 'center'),
            ('white-space', 'nowrap'),
            ('overflow', 'hidden'),
            ('text-overflow', 'ellipsis'),
            ('max-width', '200px')  # Ajuste conforme necessário
        ]
    }]))

    # Exibir a soma abaixo da tabela
    st.write(f"Total de clientes: {total_clientes}")
    st.write(f"{comissario} pagar AcquaWorld: R$ {soma_receber:.2f}")
    st.write(f"AcquaWorld pagar {comissario}: R$ {soma_pagar:.2f}")

st.write('---')

st.subheader('Acerto Comissão')


