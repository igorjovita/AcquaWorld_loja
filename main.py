import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from database import lista_vendedores, cliente, vendas, id_vendedor, id_cliente
import os
import mysql.connector
from datetime import date

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
chars2 = "')([]"
if escolha == 'Reservar':
    cursor.execute("SELECT apelido FROM vendedores")
    vendedores = cursor.fetchall()
    lista = str(vendedores).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')

    col1, col2, col3 = st.columns(3)

    with col1:
        nome_cliente = st.text_input('Nome do Cliente :')
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

        cursor.execute(
            f"SELECT COUNT(tipo) FROM reserva WHERE tipo = 'TUR2' or tipo = 'OWD' or tipo = 'ADV' or tipo = 'RESCUE' or tipo = 'REVIEW' and data = '{data}'")
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

    st.subheader('Editar Reserva')
    data_editar = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    mydb.connect()
    cursor.execute(f"SELECT id_cliente FROM reserva WHERE data = '{data_editar}'")
    id_cliente_editar = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
    lista = []
    for item in id_cliente_editar:
        st.write(item)
        cursor.execute(f"SELECT nome FROM cliente WHERE id = '{item}'")
        nome_cliente_editar = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
        st.write(nome_cliente_editar)
        lista.append(nome_cliente_editar)
        st.write(lista)
    selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista)



    # st.subheader('Editar Reserva')
    # nova_data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    # mydb.connect()
    # cursor.execute(
    #     f"select cliente.nome from reserva join cliente on cliente.id = reserva.id_cliente  where data = '{nova_data}'")
    # lista_clientes = cursor.fetchall()
    # lista = []
    # for cliente in lista_clientes:
    #     nome_cli = str(cliente).translate(str.maketrans('', '', chars))
    #     lista.append(nome_cli)
    # nome_antigo = st.selectbox('Selecione o Cliente para Editar', options=lista)
    #
    # if nome_antigo is not None:

    #     mydb.connect()
    #     cursor.execute(
    #         f"select r.data, c.nome, c.cpf, c.telefone, v.nome , r.tipo, r.fotos, c.altura, c.peso from reserva as r join cliente as c on c.id = r.id_cliente join vendedores as v on v.id = r.id_vendedor where data = '{nova_data}' and c.nome = '{nome_antigo}'")
    #     reserva_selecionada = cursor.fetchall()
    #     mydb.close()
    #     reserva = str(reserva_selecionada).translate(str.maketrans('', '', chars2)).split(',')
    #
    #     ano = (reserva[0])[13:].strip()
    #     mes = reserva[1].strip()
    #     dia = reserva[2].strip()
    #     data = f'{ano}{mes}{dia}'
    #     data_f = date.fromisoformat(data)
    #
    #     st.subheader(f"Editar a reserva de {reserva[3]}")
    #     data_nova = st.date_input('Insira a nova data', value=data_f, format='DD/MM/YYYY')
    #     nome_novo = st.text_input('Nome do Cliente', value=reserva[3])
    #     cpf_novo = st.text_input('Cpf do Cliente', value=reserva[4])
    #     telefone_novo = st.text_input('Telefone do Cliente', value=reserva[5])
    #     comissario_novo = st.text_input('Comissario', value=reserva[6])
    #     tipo_novo = st.text_input('Tipo', value=reserva[7])
    #     altura_novo = st.slider('Altura', 1.5, 2.10, value=float(reserva[9]))
    #     peso_novo = st.slider('Peso', 40, 160, value=int(reserva[10]))
    #
    #     if st.button('Editar Reserva'):
    #         mydb.connect()
    #         cursor.execute(f"SELECT id FROM cliente WHERE nome = '{nome_antigo}'")
    #         id_cliente_antigo = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))
    #         cursor.execute(f"SELECT id FROM vendedores WHERE apelido = '{comissario_novo}'")
    #         id_vendedor_novo = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
    #         st.write(id_vendedor_novo)
    #         cursor.execute(
    #             f"UPDATE reserva SET data = '{data_nova}', tipo = '{tipo_novo}', id_vendedor = '{id_vendedor_novo}' WHERE id_cliente = '{id_cliente_antigo}'")
    #         cursor.execute(
    #             f"UPDATE cliente set cpf = {cpf_novo}, nome = '{nome_novo}', telefone = '{telefone_novo}', peso = '{peso_novo}, altura = '{altura_novo}' WHERE id = {id_cliente_antigo}")
    #         mydb.close()
    #         st.success('Reserva editada com sucesso')
    #
    # else:
    #     pass

    st.write('---')

    st.subheader('Limitar Vagas')
    data_lim = st.date_input('Data da Limitação', format='DD/MM/YYYY')
    limite_bat = st.text_input('Limite de vagas para o Batismo')
    limite_cred = st.text_input('Limite de vagas para Credenciado ou Curso')
    limite_total = st.text_input('Limite de vagas totais')
    if st.button('Limitar Vagas'):
        mydb.connect()
        cursor.execute("INSERT into restricao (data, vaga_bat, vaga_cred, vaga_total) values (%s, %s, %s, %s)",
                       (data_lim, int(limite_bat), int(limite_cred), int(limite_total)))
        mydb.close()
        st.success('Limitação inserida no sistema')

    st.write('---')

if escolha == 'Visualizar':
    st.subheader('Visualizar Planilha')
    data_vis = st.date_input('Data da Visualização', format='DD/MM/YYYY')
    mydb.connect()
    cursor.execute(
        f"select c.nome, c.cpf, c.telefone, v.nome , r.tipo, r.fotos, c.altura, c.peso from reserva as r join cliente as c on c.id = r.id_cliente join vendedores as v on v.id = r.id_vendedor where data = '{data_vis}'")
    planilha = cursor.fetchall()

    df = pd.DataFrame(planilha, columns=['Nome', 'Cpf', 'Telefone', 'Comissário', 'Cert', 'Fotos', 'Altura', 'Peso'])
    st.dataframe(df, hide_index=True)
