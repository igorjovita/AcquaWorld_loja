import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import os
from datetime import timedelta, date
from functions import select_caixa, pesquisa_caixa, info_caixa

escolha = option_menu(menu_title=None, options=['Caixa Diario', 'Entrada', 'Saida'], orientation='horizontal')

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

if 'opcao_caixa' not in st.session_state:
    st.session_state.opcao_caixa = ''

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
        saida_final = 'R$ 0,00'


    elif contagem > 3:
        entradas = (str(dividido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
        entrada_final = str(entradas).replace('.', ',')
        saidas = (str(dividido[3]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
        saida_final = str(saidas).replace('.', ',')

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('ENTRADAS')
        st.subheader(entrada_final)
        if st.button('Abrir Entradas'):
            if st.session_state.opcao_caixa == 'ENTRADA':
                st.session_state.opcao_caixa = ''
            else:
                st.session_state.opcao_caixa = 'ENTRADA'

    with col2:
        st.subheader('SAIDAS')
        st.subheader(saida_final)
        if st.button('Abrir Saidas'):
            if st.session_state.opcao_caixa == 'SAIDAS':
                st.session_state.opcao_caixa = ''
            else:
                st.session_state.opcao_caixa = 'SAIDAS'

    st.data_editor(info_caixa(st.session_state.opcao_caixa))




    #     st.subheader(f'- Entradas: R$ {entrada_final}')
    #     st.subheader('- Total de Saidas : R$ 0')
    #
    #
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
