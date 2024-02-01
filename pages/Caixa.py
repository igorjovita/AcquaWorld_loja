import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import os
from datetime import timedelta, date
from functions import select_caixa, pesquisa_caixa, abrir_detalhes

escolha = option_menu(menu_title=None, options=['Caixa Diario', 'Entrada', 'Saida'], orientation='horizontal')

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered=True)

if escolha == 'Entrada':
    data = date.today()
    data_caixa = str(data).split('-')
    st.header(f'Caixa do dia {data_caixa[2]}/{data_caixa[1]}/{data_caixa[0]}')
    tipo = st.selectbox('Tipo da Entrada', options=['ENTRADA', 'BAT', 'TUR', 'ACP', 'CURSO', 'PGT PARCEIRO', 'OUTROS'])
    descrição = st.text_input('Descrição do Lançamento')
    pagamento = st.selectbox('Forma do pagamento', options=['PIX', 'DINHEIRO', 'DEBITO', 'CREDITO'])
    valor = st.text_input('Valor Pago')
    if st.button('Lançar no caixa'):
        cursor.execute(
            'insert into caixa (id_conta,data, tipo, descricao, forma_pg, valor, tipo_movimento) values ('
            '%s,%s,%s,%s,%s,%s,%s)', (1, data, tipo, descrição, pagamento, valor, 'ENTRADA'))
        mydb.commit()
    cursor.execute("select data,descricao,forma_pg, valor from caixa where tipo_movimento = 'ENTRADA'")
    dados = cursor.fetchall()
    st.dataframe(dados)

if escolha == 'Caixa Diario':
    st.header('Planilha do Caixa')
    data_caixa = st.date_input('Data', format='DD/MM/YYYY')

    dados = select_caixa(data_caixa)

    divido = str(dados).split(',')
    chars = "')([]"
    formatado = (str(divido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
    final = str(formatado).replace('.', ',')
    st.subheader(f'Saldo total do caixa : R$ {final}')

    cursor.execute(
        f"""SELECT tipo_movimento,
                SUM(CASE WHEN tipo_movimento = 'ENTRADA' 
                    THEN valor 
                    ELSE  valor 
                END) AS saldo
        FROM caixa where data = '{data_caixa}'
        GROUP BY tipo_movimento""")

    controle = cursor.fetchall()

    dividido = str(controle).split(',')
    contagem = (len(dividido))

    if contagem == 2:
        entradas = (str(dividido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
        entrada_final = str(entradas).replace('.', ',')
        col1, col2 = st.columns(2)

    with col1:
        if st.markdown("<a href='#' onclick='abrir_detalhes(\"Entradas\")' style='font-size: 30px; color: white; text-decoration: none;'>Entradas</a>", unsafe_allow_html=True):
            tipo_movimento = 'ENTRADA'
            st.table(pesquisa_caixa(data_caixa, tipo_movimento))

    with col2:
        if st.markdown("<a href='#' onclick='abrir_detalhes(\"Saídas\")' style='font-size: 30px; color: white; text-decoration: none;'>Saídas</a>", unsafe_allow_html=True):
            tipo_movimento = 'SAIDA'
            st.table(pesquisa_caixa(data_caixa, tipo_movimento))

    #     st.subheader(f'- Entradas: R$ {entrada_final}')
    #     st.subheader('- Total de Saidas : R$ 0')
    #
    # if contagem > 3:
    #     entradas = (str(dividido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
    #     entrada_final = str(entradas).replace('.', ',')
    #     saidas = (str(dividido[3]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
    #     saida_final = str(saidas).replace('.', ',')
    #     st.subheader(f'- Total de Entradas : R$ {entrada_final}')
    #     st.subheader(f'    - Total de Saidas : R$ {saida_final}')
    #
    # st.subheader('Detalhes de Entradas e Saídas:')
    # st.table(controle)

if escolha == 'Saida':
    data = date.today()
    data_caixa = str(data).split('-')
    st.header(f'Caixa do dia {data_caixa[2]}/{data_caixa[1]}/{data_caixa[0]}')
    tipo = st.selectbox('Tipo da Saida',
                        options=['Despesa Operacional', 'Café da manhã', 'Combustivel', 'Conta', 'Salario'])
    descrição = st.text_input('Descrição do Lançamento')
    pagamento = st.selectbox('Forma do pagamento', options=['PIX', 'DINHEIRO'])
    valor = st.text_input('Valor Pago')
    if st.button('Lançar no caixa'):
        cursor.execute(
            'insert into caixa (id_conta,data, tipo, descricao, forma_pg, valor, tipo_movimento) values ('
            '%s,%s,%s,%s,%s,%s,%s)', (1, data, tipo, descrição, pagamento, valor, 'SAIDA'))
