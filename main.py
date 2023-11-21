import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from database import lista_vendedores, cliente, vendas, id_vendedor, id_cliente
import os
import mysql.connector

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered=True)

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                      icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                      orientation='horizontal')

chars = "'),([]"
if escolha == 'Reservar':
    cursor.execute("SELECT apelido FROM vendedores")
    vendedores = cursor.fetchall()
    lista = str(vendedores).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')

    col1, col2, col3 = st.columns(3)

    with col1:
        nome_cliente = st.text_input('Nome do Cliente :').replace(' ', '_').capitalize()
        comissario = st.selectbox('Vendedor :', lista)

    with col2:
        cpf = st.text_input('Cpf do cliente', help='Apenas numeros')
        tipo = st.selectbox('Modalidade : ', ('', 'BAT', 'TUR1', 'TUR2', 'OWD', 'ADV'), placeholder='Vendedor')

    with col3:
        telefone_cliente = st.text_input('Telefone do Cliente :')
        valor_mergulho = st.text_input('Valor do Mergulho')

    colu1, colu2 = st.columns(2)

    with colu1:
        altura = st.slider('Altura do Cliente', 1.50, 2.10)

    with colu2:
        peso = st.slider('Peso do Cliente', 40, 160)

    colun1, colun2, colun3 = st.columns(3)

    with colun1:
        sinal = st.text_input('Valor do Sinal')

    with colun2:
        recebedor_sinal = st.selectbox('Quem recebeu o sinal?', ['', 'AcquaWorld', 'Vendedor'])

    with colun3:
        valor_loja = st.number_input('Receber na Loja :', format='%d', step=10)

    if recebedor_sinal == 'AcquaWorld':
        pago_loja = sinal
        pago_vendedor = 0

    if recebedor_sinal == 'Vendedor':
        pago_loja = 0
        pago_vendedor = sinal

    if recebedor_sinal == '':
        pago_loja = 0
        pago_vendedor = 0

    if st.button('Reservar'):
        mydb.connect()
        cursor.execute(f"SELECT COUNT(*) FROM reserva where data = '{data}'")
        contagem = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

        cursor.execute(f"SELECT * FROM restricao WHERE data = '{data}'")
        restricao = cursor.fetchone()

        cursor.execute(f"SELECT COUNT(tipo) FROM reserva WHERE tipo = 'TUR2' or tipo = 'OWD' or tipo = 'ADV' or tipo = 'RESCUE' or tipo = 'REVIEW' and data = '{data}'")
        contagem_cred = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

        lista_cred = ['TUR2', 'OWD', 'ADV', 'RESCUE', 'REVIEW']


        if restricao is None:
            vaga_cred = 8
            vaga_total = 40
            vaga_bat = vaga_total - contagem_cred
        else:
            cursor.execute(f"SELECT vaga_bat, vaga_cred, vaga_total FROM restricao WHERE data = '{data}'")
            restricoes = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
            vaga_bat = int(restricoes[0])
            vaga_cred = int(restricoes[1])
            vaga_total = int(restricoes[2])

        if contagem >= vaga_total:
            st.error('Planilha está lotada nessa data!')

        elif tipo in lista_cred and contagem_cred >= vaga_cred:
            st.write(contagem_cred)
            st.write(vaga_cred)
            st.error('Todas as vagas de credenciados foram preenchidas')

        else:
            cursor.execute("INSERT INTO cliente (cpf, nome, telefone, peso, altura) VALUES (%s, %s, %s, %s, %s)",
                           (cpf, nome_cliente, telefone_cliente, peso, altura))

            cursor.execute(f"SELECT id FROM vendedores WHERE nome = '{comissario}'")
            id_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

            cursor.execute(f"SELECT id FROM cliente WHERE cpf = {cpf}")
            id_cliente = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

            cursor.execute(
                "INSERT INTO reserva (data, id_cliente, tipo, id_vendedor,pago_loja, pago_vendedor) values (%s, %s, "
                "%s, %s, %s, %s)",
                (data, id_cliente, tipo, id_vendedor, pago_loja, pago_vendedor))
            mydb.close()
            st.success('Reserva realizada com sucesso!')
            st.write(contagem)

            st.write(vaga_bat)
            st.write(vaga_cred)
            st.write(vaga_total)

if escolha == 'Editar':

    st.subheader('Limitar Vagas')
    data_lim = st.date_input('Data da Limitação', format='DD/MM/YYYY')
    limite_bat = st.text_input('Limite de vagas para o Batismo')
    limite_cred = st.text_input('Limite de vagas para Credenciado ou Curso')
    limite_total = st.text_input('Limite de vagas totais')
    if st.button('Limitar Vagas'):
        mydb.connect()
        cursor.execute("INSERT into restricao (data, vaga_bat, vaga_cred, vaga_total) values (%s, %s, %s, %s)", (data_lim, int(limite_bat), int(limite_cred), int(limite_total)))
        mydb.close()
        st.success('Limitação inserida no sistema')

    st.write('---')
    st.subheader('Editar Reserva')
    data_ed = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    mydb.connect()
    cursor.execute("SELECT ")

if escolha == 'Visualizar':
    st.subheader('Visualizar Planilha')
    data_vis = st.date_input('Data da Visualização', format='DD/MM/YYYY')
    mydb.connect()
    cursor.execute(f"select c.nome, c.cpf, c.telefone, v.nome , r.tipo, r.fotos, c.altura, c.peso from reserva as r join cliente "
                   f"as c on c.id = r.id_cliente join vendedores as v on v.id = r.id_vendedor where data = '{data_vis}'")
    planilha = cursor.fetchall()

    df = pd.DataFrame(planilha, columns=['Nome', 'Cpf', 'Telefone', 'Comissário', 'Cert', 'Fotos', 'Altura', 'Peso'])
    st.dataframe(df)