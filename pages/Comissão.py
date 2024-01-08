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
data_inicio = st.date_input('Data inicial', format='DD/MM/YYYY', value=None)
data_final = st.date_input('Data final', format='DD/MM/YYYY', value=None)
if st.button('Pesquisar Comissão'):
    cursor.execute(f"SELECT id FROM vendedores where nome = '{comissario}'")
    id_vendedor = cursor.fetchone()[0]
    cursor.execute(f"SELECT reserva.data, reserva.nome_cliente, reserva.tipo, vendedores.nome, "
                   f"lancamento_comissao.valor_receber, lancamento_comissao.valor_pagar, lancamento_comissao.situacao "
                   f"FROM reserva JOIN lancamento_comissao ON reserva.id = lancamento_comissao.id_reserva JOIN "
                   f"vendedores on lancamento_comissao.id_vendedor = vendedores.id WHERE reserva.data BETWEEN '"
                   f"{data_inicio}' and '{data_final}' and lancamento_comissao.id_vendedor = {id_vendedor}")
    resultados = cursor.fetchall()

    df = pd.DataFrame(resultados, columns=['Data', 'Nome Cliente', 'Tipo', 'Vendedor', 'Valor a Receber', 'Valor a Pagar', 'Situação'])
    df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
    soma_clientes = df['Nome Cliente'].nunique()
    soma_receber = df['Valor a Receber'].sum()
    soma_pagar = df['Valor a Pagar'].sum()
    df_soma = pd.DataFrame({'Data': ['Total'], 'Nome Cliente': f'{soma_clientes} clientes', 'Valor a Receber': f'R$ {soma_receber:.2f}', 'Valor a Pagar': f'R$ {soma_pagar:.2f}'})
    df_final = pd.concat([df, df_soma])
    st.table(df_final.style.format({
        'Valor Receber': 'R${:,.2f}',
        'Valor Pagar': 'R${:,.2f}'
    }).hide_index().set_properties(**{'text-align': 'center'}).set_table_styles([{
        'selector': 'th',
        'props': [
            ('text-align', 'center'),
            ('white-space', 'nowrap'),
            ('overflow', 'hidden'),
            ('text-overflow', 'ellipsis'),
            ('max-width', '200px')  # Ajuste conforme necessário
        ]
    }]))

