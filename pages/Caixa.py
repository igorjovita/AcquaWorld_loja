import streamlit as st
from streamlit_option_menu import option_menu
import mysql.connector
import os

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
    data = st.date_input('Selecione a data', format='DD/MM/YYYY')
    st.header(f'Caixa do dia {data}')
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
    cursor.execute(

        """SELECT id_conta,
                SUM(CASE WHEN tipo_movimento = 'ENTRADA' 
                    THEN valor 
                    ELSE - valor 
                END) AS saldo
        FROM caixa""")

    dados = cursor.fetchall()

    divido = str(dados).split(',')
    chars = "')([]"
    formatado = (str(divido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
    final = str(formatado).replace('.', ',')
    st.subheader(f'Saldo total do caixa : R$ {final}')

    cursor.execute(

        """SELECT tipo_movimento,
                SUM(CASE WHEN tipo_movimento = 'ENTRADA' 
                    THEN valor 
                    ELSE  valor 
                END) AS saldo
        FROM caixa 
        GROUP BY tipo_movimento""")
    controle = cursor.fetchall()
    st.write(controle)
    if controle is not None:

        dividido = str(controle).split(',')

        saidas = (str(dividido[3]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
        entradas = (str(dividido[1]).replace('Decimal', '').translate(str.maketrans('', '', chars)))
        saida_final = str(saidas).replace('.', ',')
        entrada_final = str(entradas).replace('.', ',')
        st.subheader(f'    - Total de Entradas : R$ {entrada_final}')
        st.subheader(f'    - Total de Saidas : R$ {saida_final}')

if escolha == 'Saida':
    data = st.date_input('Selecione a data', format='DD/MM/YYYY')
    st.header(f'Caixa do dia {data}')
    tipo = st.selectbox('Tipo da Saida',
                        options=['Despesa Operacional', 'Café da manhã', 'Combustivel', 'Conta', 'Salario'])
    descrição = st.text_input('Descrição do Lançamento')
    pagamento = st.selectbox('Forma do pagamento', options=['PIX', 'DINHEIRO'])
    valor = st.text_input('Valor Pago')
    if st.button('Lançar no caixa'):
        cursor.execute(
            'insert into caixa (id_conta,data, tipo, descricao, forma_pg, valor, tipo_movimento) values ('
            '%s,%s,%s,%s,%s,%s,%s)', (1, data, tipo, descrição, pagamento, valor, 'SAIDA'))

