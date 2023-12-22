import base64

import pdfkit
import jinja2
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
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

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                      icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                      orientation='horizontal')

pasta = os.path.dirname(__file__)


# Inicializar listas


def gerar_pdf(self):
    mydb.connect()

    # Consulta ao banco de dados para obter os dados
    cursor.execute(
        f"SELECT nome_cliente FROM reserva WHERE data = '{data_para_pdf}'")
    lista_cliente = cursor.fetchall()
    cliente = []
    for item1 in lista_cliente:
        id_cli = str(item1).translate(str.maketrans('', '', chars))
        cliente.append(id_cli)

    cpf = []
    for nome in cliente:
        cursor.execute(
            f"SELECT cpf FROM cliente WHERE nome = '{nome}'")
        lista_cpf = cursor.fetchall()

        for item in lista_cpf:
            nome = str(item).translate(str.maketrans('', '', chars2))
            cpf.append(nome)

    telefone = []
    for nome in cliente:
        cursor.execute(
            f"SELECT telefone FROM cliente WHERE nome = '{nome}'")
        lista_telefone = cursor.fetchall()
        for item in lista_telefone:
            nome = str(item).translate(str.maketrans('', '', chars2))
            telefone.append(nome)

    comissario = []
    lista_id_vendedor = []
    cursor.execute(
        "SELECT id_vendedor FROM reserva WHERE data = %s", (data_para_pdf,))
    lista_comissario = cursor.fetchall()

    for item in lista_comissario:
        id_vend = str(item).translate(str.maketrans('', '', chars2))
        lista_id_vendedor.append(id_vend)
        for id_v in lista_id_vendedor:
            cursor.execute(f"SELECT apelido from vendedores where id = '{id_v}'")
            nome = str(cursor.fetchone()).translate(str.maketrans('', '', chars2))
            comissario.append(nome)

    mydb.close()
    mydb.connect()

    cert = []
    cursor.execute(
        "SELECT tipo FROM reserva WHERE data = %s", (data_para_pdf,))
    lista_cert = cursor.fetchall()
    for item in lista_cert:
        nome = str(item).upper().translate(str.maketrans('', '', chars2))
        cert.append(nome)

    foto = []
    cursor.execute(
        "SELECT fotos FROM reserva WHERE data = %s", (data_para_pdf,))
    lista_foto = cursor.fetchall()

    for item in lista_foto:
        nome = str(item).upper().translate(str.maketrans('', '', chars2))
        foto.append(nome)

    cursor.execute(
        "SELECT  dm FROM reserva WHERE data = %s", (data_para_pdf,))
    lista_dm = cursor.fetchall()
    dm = []
    for item in lista_dm:
        nome = str(item).upper().translate(str.maketrans('', '', chars2))
        dm.append(nome)

    roupa = []
    for nome in cliente:
        cursor.execute(
            f"SELECT roupa FROM cliente WHERE nome = '{nome}'")
        lista_roupa = cursor.fetchall()

        for item in lista_roupa:
            nome = str(item).upper().translate(str.maketrans('', '', chars2))
            roupa.append(nome)

    background_colors = []
    cursor.execute(
        "SELECT check_in FROM reserva WHERE data = %s", (data_para_pdf,))
    lista_check_in = cursor.fetchall()

    for item in lista_check_in:
        nome = str(item).translate(str.maketrans('', '', chars2))
        background_colors.append(nome)

    # Processar a data
    data_selecionada = str(data_para_pdf).split('-')
    dia, mes, ano = data_selecionada[2], data_selecionada[1], data_selecionada[0]
    data_completa = f'{dia}/{mes}/{ano}'

    # Criar o contexto
    contexto = {'cliente': cliente, 'cpf': cpf, 'tel': telefone, 'comissario': comissario, 'c': cert, 'f': foto,
                'r': roupa, 'data_reserva': data_completa, 'background_colors': background_colors, 'dm': dm}

    # Renderizar o template HTML
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha.html')
    output_text = planilha.render(contexto)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_para_pdf}.pdf"
    # Caminho completo do arquivo
    pdf_path = os.path.join(os.getcwd(), pdf_filename)

    # Verificar se o arquivo já existe
    if os.path.exists(pdf_path):
        # Se existir, remova-o antes de salvar o no vo
        os.remove(pdf_path)

    # Gerar PDF
    config = pdfkit.configuration()
    pdfkit.from_string(output_text, pdf_filename, configuration=config)

    download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_filename, "rb").read()).decode()}" download="{pdf_filename}">Clique aqui para baixar</a>'
    st.markdown(download_link, unsafe_allow_html=True)

    # Fechar a conexão
    mydb.close()
    return pdf_filename, output_text  # ou gcs_pdf_filename se preferir



if escolha == 'Visualizar':
    # Função para obter cores com base no valor da coluna 'check_in'

    data_planilha = st.date_input('Data da Planilha')
    # Exibir tabela estilizada no Streamlit
    tabela_html = gerar_pdf(data_planilha)
    st.markdown(tabela_html, unsafe_allow_html=True)
    st.write('---')

    # Formulário para gerar PDF
    data_para_pdf = st.date_input("Data para gerar PDF:")
    if st.button("Gerar PDF"):
        pdf_filename = gerar_pdf(data_para_pdf)
        st.download_button('Planilha', gerar_pdf(data_para_pdf))

if escolha == 'Reservar':
    mydb.connect()
    cursor.execute("SELECT apelido FROM vendedores")
    lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
    st.subheader('Reservar Clientes')

    data = st.date_input('Data da Reserva', format='DD/MM/YYYY')

    col1, col2, col3 = st.columns(3)

    with col1:
        nome_cliente = st.text_input('Nome do Cliente :')
        comissario = st.selectbox('Vendedor :', lista_vendedor)

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
            roupa = f'{altura}/{peso}'
            cursor.execute("INSERT INTO cliente (cpf, nome, telefone, roupa) VALUES (%s, %s, %s, %s)",
                           (cpf, nome_cliente, telefone_cliente, roupa))

            cursor.execute(f"SELECT id FROM vendedores WHERE nome = '{comissario}'")
            id_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

            cursor.execute(f"SELECT id FROM cliente WHERE cpf = {cpf}")
            id_cliente = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

            cursor.execute(
                "INSERT INTO reserva (data, id_cliente, tipo, id_vendedor,pago_loja, pago_vendedor, valor_total,nome_cliente,check_in) values (%s, %s, %s, %s, "
                "%s, %s, %s, %s, %s)",
                (data, id_cliente, tipo, id_vendedor, pago_loja, pago_vendedor, valor_mergulho, nome_cliente, 'Branco'))
            mydb.close()
            st.success('Reserva realizada com sucesso!')

if escolha == 'Editar':

    data_editar = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    mydb.connect()
    cursor.execute(f"SELECT id_cliente FROM reserva WHERE data = '{data_editar}'")
    id_cliente_editar = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
    lista = []
    for item in id_cliente_editar:
        cursor.execute(f"SELECT nome FROM cliente WHERE id = '{item}'")
        nome_cliente_editar = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
        lista.append(nome_cliente_editar)
    selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista)

    if selectbox_cliente is not None:
        st.subheader(f'Editar a reserva de {selectbox_cliente}')
        cursor.execute(f"SELECT id, cpf, telefone, peso, altura FROM cliente WHERE nome = '{selectbox_cliente}'")
        info_cliente = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
        cursor.execute(f"SELECT tipo, id_vendedor from reserva where id_cliente = '{info_cliente[0]}'")
        info_reserva = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

        escolha_editar = st.radio('Escolha o que deseja editar',
                                  ['Data', 'Nome', 'CPF e Telefone', 'Vendedor', 'Certificação', 'Peso e Altura'])

        if escolha_editar == 'Data':
            nova_data = st.date_input('Nova Data da reserva', format='DD/MM/YYYY')
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(f"UPDATE reserva SET data = '{nova_data}' WHERE id_cliente = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')
        if escolha_editar == 'Nome':
            nome_novo = st.text_input('Nome do Cliente', value=selectbox_cliente)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(f"UPDATE cliente SET nome = '{nome_novo}' WHERE id = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')
        if escolha_editar == 'CPF e Telefone':
            cpf_novo = st.text_input('Cpf do Cliente', value=info_cliente[1])
            telefone_novo = st.text_input('Telefone do Cliente', value=info_cliente[2])
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE cliente SET cpf = '{cpf_novo}', telefone = '{telefone_novo}' WHERE id = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')
        if escolha_editar == 'Vendedor':
            mydb.connect()
            cursor.execute("SELECT apelido FROM vendedores")
            lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
            cursor.execute(f"SELECT apelido FROM vendedores WHERE id = '{info_reserva[1]}'")
            comissario_antigo = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
            st.subheader(f'Vendedor : {comissario_antigo}')
            comissario_novo = st.selectbox('Selecione o novo vendedor', lista_vendedor)
            if st.button('Atualizar Reserva'):
                cursor.execute(f"SELECT id FROM vendedores WHERE apelido = '{comissario_novo}'")
                id_vendedor_editar = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
                cursor.execute(
                    f"UPDATE reserva SET id_vendedor = '{id_vendedor_editar}' WHERE id_cliente = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')

        if escolha_editar == 'Certificação':
            st.subheader(f'Certificação: {info_reserva[0]}')
            tipo_novo = st.selectbox('Nova Certificação', ['', 'BAT', 'TUR1', 'TUR2', 'OWD', 'ADV'])
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE reserva SET tipo = '{tipo_novo}' WHERE id_cliente = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')
        if escolha_editar == 'Peso e Altura':
            peso_novo = st.slider('Peso do CLiente', value=int(info_cliente[3]), min_value=40, max_value=160)
            altura_novo = st.slider('Altura do CLiente', value=float(info_cliente[4]), min_value=1.50, max_value=2.10)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE cliente SET peso = '{peso_novo}', altura = '{altura_novo}' WHERE id = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')

if escolha == 'Pagamento':
    data_pagamento = date.today()
    data_reserva = st.date_input('Data da reserva', format='DD/MM/YYYY')

    lista_pagamento = []
    mydb.connect()
    cursor.execute(f"SELECT id_cliente FROM reserva WHERE data = '{data_reserva}'")
    id_cliente_pagamento = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
    for item in id_cliente_pagamento:
        cursor.execute(f"SELECT nome FROM cliente WHERE id = '{item}'")
        nome_cliente_pagamento = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
        lista_pagamento.append(nome_cliente_pagamento)

    selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista_pagamento)

    forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'], index=None,
                            placeholder='Insira a forma de pagamento')

    if forma_pg == 'Credito':
        parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)
    else:
        parcela = 0

    pagamento = st.text_input('Valor pago')
    check_in_entry = st.selectbox('Cliente vai pra onde?', ['Loja', 'Para o pier'], index=None)
    if check_in_entry == 'Loja':
        check_in = 'Azul'
    if check_in_entry == 'Para o pier':
        check_in = 'Amarelo'

    if st.button('Lançar Pagamento'):
        mydb.connect()
        cursor.execute(f"SELECT id FROM cliente WHERE nome = '{selectbox_cliente}'")
        id_cliente_pagamento2 = str(cursor.fetchone()).translate(str.maketrans('', '', chars))

        cursor.execute(
            f"SELECT id, id_vendedor, pago_loja, pago_vendedor, tipo, valor_total  FROM reserva WHERE id_cliente = '{id_cliente_pagamento2}' and data = '{data_reserva}'")
        info_reserva_pg = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

        cursor.execute(f"SELECT valor_neto FROM vendedores WHERE id = {info_reserva_pg[1]}")
        valor_neto = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

        cursor.execute(f"UPDATE reserva set check_in = '{check_in}' where nome_cliente = '{selectbox_cliente}'")

        sinal_loja = float(str(info_reserva_pg[2]).strip('Decimal'))
        sinal_vendedor = float(str(info_reserva_pg[3]).strip('Decimal'))
        total_mergulho = float(str(info_reserva_pg[5]).strip('Decimal'))
        st.write(sinal_loja)
        st.write(sinal_vendedor)
        st.write(float(pagamento))
        st.write(valor_neto)
        pagoloja = float(pagamento) + sinal_loja

        if pagoloja > valor_neto:
            valor_receber = 0
            valor_pagar = pagoloja - valor_neto

        if pagoloja == valor_neto and sinal_vendedor == total_mergulho - valor_neto:
            valor_receber = 0
            valor_pagar = 0

        if pagoloja == valor_neto and sinal_vendedor != total_mergulho - valor_neto:
            valor_receber = 0
            valor_pagar = sinal_vendedor - (total_mergulho - valor_neto)

        if pagoloja < valor_neto and sinal_vendedor == total_mergulho - valor_neto:
            valor_receber = (float(pagamento) + sinal_loja) - valor_neto
            valor_pagar = 0

        if pagoloja < valor_neto and sinal_vendedor != total_mergulho - valor_neto:
            valor_receber = (float(pagamento) + sinal_loja) - valor_neto
            valor_pagar = valor_receber + (-sinal_vendedor)

        st.write(f'Valor Receber - R$ {valor_receber}')

        st.write(f'Valor a pagar - R$ {valor_pagar}')

        data_completa = str(data_reserva).split('-')
        descricao = f'{selectbox_cliente} do dia {data_completa[2]}/{data_completa[1]}/{data_completa[0]}'

        cursor.execute(
            "INSERT INTO pagamentos (data, data_reserva ,id_reserva, id_vendedor, sinal_loja, sinal_vendedor, pagamento, forma_pg, parcela) VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)",
            (
                data_pagamento, data_reserva, info_reserva_pg[0], info_reserva_pg[1], sinal_loja, sinal_vendedor,
                pagamento,
                forma_pg, parcela))
        cursor.execute(
            "INSERT INTO caixa (id_conta, data, tipo_movimento, tipo, descricao, forma_pg, valor) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (1, data_pagamento, 'ENTRADA', info_reserva_pg[4], descricao, forma_pg, pagamento))
        # cursor.execute(f"SELECT id FROM pagamentos WHERE id_reserva = {info_reserva_pg[0]}")
        # id_pagamento = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
        # cursor.execute("INSERT INTO lancamento_comissao (id_reserva, id_vendedor, id_pagamento, valor_receber, valor_pagar, situacao) VALUES (%s, %s, %s, %s, %s, %s)", (info_reserva_pg[0], info_reserva_pg[1], id_pagamento,))

        mydb.close()
        st.success('Pagamento lançado no sistema!')

#
#     st.write('---')
#
#     st.subheader('Limitar Vagas')
#     data_lim = st.date_input('Data da Limitação', format='DD/MM/YYYY')
#     limite_bat = st.text_input('Limite de vagas para o Batismo')
#     limite_cred = st.text_input('Limite de vagas para Credenciado ou Curso')
#     limite_total = st.text_input('Limite de vagas totais')
#     if st.button('Limitar Vagas'):
#         mydb.connect()
#         cursor.execute("INSERT into restricao (data, vaga_bat, vaga_cred, vaga_total) values (%s, %s, %s, %s)",
#                        (data_lim, int(limite_bat), int(limite_cred), int(limite_total)))
#         mydb.close()
#         st.success('Limitação inserida no sistema')
#
#     st.write('---')
#
