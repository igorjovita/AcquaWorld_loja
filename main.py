import base64

import pandas as pd
from babel.numbers import format_currency
from mysql.connector import IntegrityError
import streamlit as st
from streamlit_option_menu import option_menu
import os
import mysql.connector
import streamlit.components.v1
from functions import select_reserva, processar_pagamento, gerar_pdf, gerar_html, select_apelido_vendedores, \
    calculo_restricao, insert_cliente, insert_reserva, select_id_vendedores, insert_lancamento_comissao, \
    select_valor_neto, select_cliente, select_grupo_reserva, update_vaga, select_id_cliente_like, \
    select_nome_id_titular, select_reserva_id_titular, titulo_tabela_pagamentos, select_pagamentos, \
    insert_controle_curso, select_maquina
import time

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout='wide', page_title='AcquaWorld', page_icon='🤿')

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)

with st.sidebar:
    st.write('Login')
    authenticator.login()

chars = "'),([]"
chars2 = "')([]"

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem",
    charset="utf8")

cursor = mydb.cursor(buffered=True)


menu_main = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                        icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                        orientation='horizontal')

pasta = os.path.dirname(__file__)

if menu_main == 'Visualizar': # PARTE OK
    # Função para obter cores com base no valor da coluna 'check_in'
    data_para_pdf = st.date_input("Data para gerar PDF:", format='DD/MM/YYYY')

    coluna1, coluna2 = st.columns(2)

    with coluna1:
        botao1 = st.button('Gerar Html')

    with coluna2:
        botao2 = st.button("Gerar PDF")

    if botao1:
        tabela_html = gerar_html(data_para_pdf)
        st.components.v1.html(tabela_html, height=1000, width=1000, scrolling=True)

    if botao2:
        pdf_filename = gerar_pdf(data_para_pdf)
        download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_filename, "rb").read()).decode()}" download="{pdf_filename}">Clique aqui para baixar</a>'
        st.markdown(download_link, unsafe_allow_html=True)

# Formulário para gerar PDF


if menu_main == 'Reservar':
    # Inicialização de listas e variaveis
    nomes_clientes = []
    reservas = []
    nomes_titulares = []
    id_titular = None
    id_cliente = None
    # Inicializaçao de session_state

    if 'ids_clientes' not in st.session_state:
        st.session_state['ids_clientes'] = []

    if 'valor_sinal' not in st.session_state:
        st.session_state.valor_sinal = 0

    if 'valor_mergulho_total' not in st.session_state:
        st.session_state.valor_mergulho_total = 0

    if 'valor_mergulho_receber' not in st.session_state:
        st.session_state.valor_mergulho_receber = 0

    if 'botao_clicado' not in st.session_state:
        st.session_state.botao_clicado = False

    if 'nome_dependente' not in st.session_state:
        st.session_state.nome_dependente = []

    if 'pagamentos' not in st.session_state:
        st.session_state.pagamentos = []

    if 'pagamentos2' not in st.session_state:
        st.session_state.pagamentos2 = []

    if 'nome_cadastrado' not in st.session_state:
        st.session_state.nome_cadastrado = []

    if 'data_pratica2' not in st.session_state:
        st.session_state.data_pratica2 = []

    # Capturar nome dos vendedores cadastrados no sistema
    mydb.connect()
    lista_vendedor = select_apelido_vendedores()

    st.subheader('Reservar Cliente')

    col1, col2, = st.columns(2)

    with col1:
        data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
        comissario = st.selectbox('Vendedor:', lista_vendedor, index=None, placeholder='Escolha o vendedor')

    with col2:
        quantidade_reserva = st.number_input('Quantidade de Reservas', min_value=0, value=0, step=1)
        reserva_conjunta = st.selectbox('Agrupar reserva a Titular já reservado?', ['Não', 'Sim'])

    if reserva_conjunta == 'Sim':
        with mydb.cursor() as cursor:
            cursor.execute(
                f"SELECT id_cliente, nome_cliente FROM reserva WHERE id_titular = id_cliente AND data = '{data}'")
            resultados = cursor.fetchall()
            for resultado in resultados:
                id_cliente_conjunto, nome_cliente_conjunto = resultado
                nomes_titulares.append(nome_cliente_conjunto)

            with col1:
                titular = st.selectbox('Escolha o titular', options=nomes_titulares, index=None)

            # Validar a seleção do titular antes de prosseguir
            if not titular:
                st.warning('Selecione o titular antes de adicionar clientes adicionais.')
            else:
                for i in range(quantidade_reserva):
                    # Campo de entrada para o nome do cliente
                    nome_cliente = st.text_input(f'Nome do Cliente {i + 1}:').capitalize()
                    nomes_clientes.append(nome_cliente)
    else:
        # Loop para os demais clientes
        for i in range(quantidade_reserva):
            # Campo de entrada para o nome do cliente
            nome_cliente = st.text_input(f'Nome do Cliente {i + 1}:').title()
            nomes_clientes.append(nome_cliente)
    coluna1, coluna2 = st.columns(2)

    with coluna1:
        botao1 = st.button('Inserir dados do cliente')
    if botao1:
        contagem, restricao, contagem_cred, vaga_bat, vaga_cred, vaga_total = calculo_restricao(data)

        if comissario is None:
            st.error('Insira o nome do comissario')
        elif contagem >= vaga_total:
            st.error('Planilha está lotada nessa data!')
        else:
            st.session_state.botao_clicado = True

    with coluna2:
        botao2 = st.button('Segurar vagas')

    if botao2:
        if comissario is None:
            st.error('Insira o nome do comissario')
        else:
            id_vendedor = select_id_vendedores(comissario)

        reserva_temporaria = []
        for i, valor in enumerate(range(quantidade_reserva)):
            id_cliente = insert_cliente('', f'{data}/{comissario}/{i}', '', '')

            if valor == 0:
                id_titular_vaga = id_cliente
            reserva_temporaria.append(
                (data, id_cliente, '', id_vendedor, '', f'{data}/{comissario}/{i}', '', id_titular_vaga, ''))

        for reserva in reserva_temporaria:
            insert_reserva(reserva)

        st.success(f'{quantidade_reserva} vagas reservadas para  {comissario}')

    if st.session_state.botao_clicado:

        # Exibir os campos adicionais para cada reserva
        for i, nome_cliente in enumerate(nomes_clientes):

            if reserva_conjunta == 'Sim':
                nome_titular = titular

            if i == 0 and reserva_conjunta == 'Não':
                titulo = f'Reserva Titular: {nome_cliente}'
                subtitulo = 'Para acessar essa reserva posteriormente use o nome do titular!'
                nome_titular = nome_cliente
            else:
                titulo = f'Reserva  Cliente: {nome_cliente}'
                subtitulo = ''
            with st.form(f'Fomulario - {nome_cliente}'):
                st.subheader(titulo)
                st.text(subtitulo)
                colu1, colu2, colu3 = st.columns(3)

                with colu1:
                    cpf = st.text_input(f'Cpf', help='Apenas números',
                                        key=f'cpf{nome_cliente}{i}')
                    altura = st.slider(f'Altura', 1.50, 2.10,
                                       key=f'altura{nome_cliente}{i}')
                    sinal = st.text_input(f'Valor do Sinal', key=f'sinal{nome_cliente}{i}', value=0)

                with colu2:
                    telefone = st.text_input(f'Telefone:',
                                             key=f'telefone{nome_cliente}{i}')
                    peso = st.slider(f'Peso', 40, 160, key=f'peso{nome_cliente}{i}')
                    recebedor_sinal = st.selectbox(f'Recebedor do Sinal',
                                                   ['AcquaWorld', 'Vendedor'],
                                                   index=None,
                                                   placeholder='Recebedor do Sinal',
                                                   key=f'recebedor{nome_cliente}{i}')
                with colu3:
                    tipo = st.selectbox(f'Certificação: ',
                                        ('BAT', 'ACP', 'TUR1', 'TUR2', 'OWD', 'ADV', 'EFR', 'RESCUE', 'DM'),
                                        index=None, placeholder='Certificação', key=f'tipo{nome_cliente}{i}')
                    valor_mergulho = st.text_input(f'Valor do Mergulho',
                                                   key=f'valor{nome_cliente}{i}')
                    valor_loja = st.text_input(f'Valor a receber:', key=f'loja{nome_cliente}{i}')

                with st.expander('Data Pratica 2'):
                    data_pratica2 = st.date_input('Data da Pratica 2', format='DD/MM/YYYY', value=None)
                    if data_pratica2 == '0000-00-00':
                        data_pratica2 = ''

                    roupa = f'{altura:.2f}/{peso}'
                    if valor_loja == '':
                        valor_loja = 0.00
                    else:
                        valor_loja = valor_loja
                if st.form_submit_button(f'Cadastrar {nome_cliente}'):
                    lista_cred = ['TUR2', 'OWD', 'ADV', 'RESCUE', 'REVIEW']
                    contagem, restricao, contagem_cred, vaga_bat, vaga_cred, vaga_total = calculo_restricao(data)

                    if tipo in lista_cred and contagem_cred >= vaga_cred:
                        st.write(contagem_cred)
                        st.write(vaga_cred)
                        st.write(restricao)
                        st.error('Todas as vagas de credenciados foram preenchidas')

                    elif (tipo == 'OWD' or tipo == 'ADV') and data_pratica2 is None:
                        st.error('Informe a data da pratica 2')
                    else:

                        if nome_cliente not in st.session_state.nome_cadastrado:
                            st.session_state.nome_cadastrado.append(nome_cliente)
                            forma_pg = 'Pix'
                            st.session_state.pagamentos.append((data, recebedor_sinal, sinal, forma_pg))
                            st.session_state.valor_sinal += float(sinal)

                            st.session_state.valor_mergulho_receber += float(valor_loja)
                            st.session_state.valor_mergulho_total += float(valor_mergulho)

                            if i != 0:
                                st.session_state.nome_dependente.append(nome_cliente)

                            with mydb.cursor() as cursor:
                                try:

                                    id_cliente = insert_cliente(cpf, nome_cliente, telefone, roupa)
                                    st.session_state.ids_clientes.append(id_cliente)
                                    mydb.commit()

                                except IntegrityError:
                                    cursor.execute(f"SELECT id from cliente where cpf = %s and nome = %s",
                                                   (cpf, nome_cliente))
                                    info_registro = cursor.fetchone()

                                    if info_registro:
                                        id_cliente = info_registro[0]
                                        st.session_state.ids_clientes.append(id_cliente)
                        else:
                            st.error(f'{nome_cliente} já foi cadastrado no sistema!')

            # Adicione esta verificação antes de tentar acessar a lista
            if i < len(st.session_state['ids_clientes']):
                id_cliente = st.session_state['ids_clientes'][i]

            else:
                pass

            with mydb.cursor() as cursor:

                id_vendedor = select_id_vendedores(comissario)

                if reserva_conjunta == 'Sim':

                    cursor.execute(f"SELECT id_cliente from reserva where nome_cliente = '{titular}'")
                    id_titular = cursor.fetchone()[0]

                else:
                    if id_titular is None:
                        id_titular = id_cliente

            reservas.append(
                (data, id_cliente, tipo, id_vendedor, valor_mergulho, nome_cliente, '#FFFFFF', id_titular,
                 valor_loja, data_pratica2))
            st.write('---')

        if st.button('Reservar'):

            with mydb.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM reserva WHERE id_cliente = %s and data = %s",
                               (id_cliente, data))
                verifica_cpf = cursor.fetchone()[0]

                if verifica_cpf > 0:
                    st.error('Cliente já reservado para esta data')
                    reservas = []

                else:
                    for reserva in reservas:
                        id_reserva = insert_reserva(reserva)
                        if reserva[2] == 'OWD' or reserva[2] == 'ADV' or reserva[2] == 'EFR' or reserva[
                            2] == 'RESCUE' or reserva[2] == 'DM':
                            insert_controle_curso(reserva[0], reserva[9], reserva[1], reserva[2])

                        st.session_state.pagamentos2.append((id_titular, id_reserva))

                    for i in range(len(st.session_state.pagamentos)):
                        st.session_state.pagamentos[i] = st.session_state.pagamentos[i] + \
                                                         st.session_state.pagamentos2[i]

                    if recebedor_sinal is not None:

                        for pagamento in st.session_state.pagamentos:
                            cursor.execute(
                                "INSERT INTO pagamentos (data, recebedor, pagamento, forma_pg, id_titular, id_reserva) VALUES (%s,%s, %s, %s, %s, %s)",
                                pagamento)
                        st.session_state['ids_clientes'] = []

                    if recebedor_sinal == 'Vendedor' and valor_mergulho == sinal:
                        forma_pg = 'Pix'
                        valor_neto = select_valor_neto(tipo, valor_total_reserva=valor_mergulho,
                                                       id_vendedor_pg=id_vendedor, forma_pg=forma_pg)

                        lista_ids = []
                        for tupla in st.session_state.pagamentos2:
                            lista_ids.append(tupla[1])

                        for dado in lista_ids:
                            insert_lancamento_comissao(id_reserva_cliente=dado, id_vendedor_pg=id_vendedor,
                                                       valor_receber=valor_neto, valor_pagar=0,
                                                       id_titular_pagamento=id_titular)

                        reservas = []

                    data_ = str(data).split('-')
                    data_formatada = f'{data_[2]}/{data_[1]}/{data_[0]}'

                    descricao = f'Sinal reserva titular {nome_titular} dia {data_formatada}'
                    forma_pg = 'Pix'

                    # Formatando as variáveis como moeda brasileira
                    valor_sinal_formatado = format_currency(st.session_state.valor_sinal, 'BRL', locale='pt_BR')
                    valor_mergulho_receber_formatado = format_currency(st.session_state.valor_mergulho_receber,
                                                                       'BRL',
                                                                       locale='pt_BR')
                    valor_mergulho_total_formatado = format_currency(st.session_state.valor_mergulho_total,
                                                                     'BRL',
                                                                     locale='pt_BR')
                    tipo_sinal = 'SINAL'
                    if recebedor_sinal == 'AcquaWorld':
                        cursor.execute(
                            "INSERT INTO caixa (tipo, data, tipo_movimento, descricao, forma_pg, valor) VALUES (%s,     %s, %s, %s, %s, %s)",
                            (tipo_sinal, data, 'ENTRADA', descricao, forma_pg, st.session_state.valor_sinal))

                    # Na hora de exibir, utilize a vírgula para juntar os nomes dos dependentes
                    nomes_dependentes_formatados = ', '.join(st.session_state.nome_dependente)

                    st.success('Reserva realizada com sucesso!')

                    st.code(f"""
                    *Reserva Concluida com Sucesso!*
                    
                    Titular da Reserva - {nome_titular}
                    Reservas Dependentes - {nomes_dependentes_formatados}
                    
                    Valor total - {valor_mergulho_total_formatado}
                    Já foi pago - {valor_sinal_formatado}
                    Falta pagar - {valor_mergulho_receber_formatado}

                    
                    Favor chegar na data marcada: 

                    ⚠️ {data_formatada} às 07:30hs em nossa loja 
                    
                    ⚠️ Favor chegar na hora pois é necessário, efetuar o restante do pagamento caso ainda não tenha feito, preencher os termos de responsabilidade/questionário médico e fazer retirada da pulseirinha que dá acesso à embarcação.
                    
                    ⚓ O ponto de encontro será na loja de mergulho !⚓
                    
                    ➡️ARRAIAL DO CABO: Praça da Bandeira, n 23, Praia dos Anjos. Loja de Madeira na esquina, um pouco depois da rodoviária Indo pra praia dos anjos.

                    *Na Marina dos Anjos, a prefeitura cobra uma taxa de  embarque de R$ 10,00,  por pessoa em dinheiro.*
                    """)
                    st.session_state.valor_sinal = 0
                    st.session_state.valor_mergulho_receber = 0
                    st.session_state.valor_mergulho_total = 0
                    st.session_state.nome_dependente = []
                    st.session_state.pagamentos = []
                    st.session_state.pagamentos2 = []

            if 'botao_clicado' in st.session_state:
                st.session_state.botao_clicado = False

if menu_main == 'Editar':

    data_editar = st.date_input('Data da Reserva', format='DD/MM/YYYY')
    opcoes = st.radio('Filtro', ['Editar Grupo', 'Editar Reserva'], horizontal=True)
    mydb.connect()
    lista = []
    lista2 = []
    if 'info_editar' not in st.session_state:
        st.session_state.info_editar = []
    if opcoes == 'Editar Reserva':
        cursor.execute(f"SELECT nome_cliente FROM reserva WHERE data = '{data_editar}'")
        id_cliente_editar = cursor.fetchall()
        for dado in id_cliente_editar:
            lista.append(str(dado).translate(str.maketrans('', '', chars)))
    else:
        cursor.execute(
            f"SELECT nome_cliente, id_cliente FROM reserva WHERE data = '{data_editar}' and id_cliente = id_titular")
        id_cliente_editar = cursor.fetchall()
        for dado in id_cliente_editar:
            lista.append(str(dado[0]).translate(str.maketrans('', '', chars)))
            st.session_state.info_editar.append(dado)

    selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista)

    if selectbox_cliente is not None:
        if opcoes == 'Editar Reserva':
            st.subheader(f'Editar a reserva de {selectbox_cliente}')
        else:
            st.subheader(f'Editar reservas do grupo de {selectbox_cliente}')
            info_titular = select_reserva(selectbox_cliente, data_editar)
            id_titular_reserva = info_titular[1]
            id_grupo_reserva = select_grupo_reserva(id_titular_reserva, data_editar)
            for id_cliente in id_grupo_reserva:
                if id_cliente:
                    cliente = select_cliente(id_cliente[0])
                    # Verifica se o primeiro elemento (CPF) existe e não é nulo
                    cpf = cliente[0] if cliente[0] else ''
                    # Verifica se o segundo elemento (telefone) existe e não é nulo
                    telefone = cliente[1] if len(cliente) > 1 and cliente[1] else ''
                    # Verifica se o terceiro elemento (roupa) existe e não é nulo
                    roupa = cliente[2] if len(cliente) > 2 and cliente[2] else ''
                else:
                    # Caso a lista cliente esteja vazia ou nula, atribui valores padrão vazios
                    cpf = ''
                    telefone = ''
                    roupa = ''

        info_reserva = select_reserva(selectbox_cliente, data_editar)
        id_cliente = info_reserva[1]
        cpf_cliente, telefone_cliente, roupa_cliente = select_cliente(id_cliente)

        escolha_editar = st.radio('Escolha o que deseja editar',
                                  ['Data', 'Nome', 'CPF e Telefone', 'Vendedor', 'Certificação', 'Peso e Altura'])

        if escolha_editar == 'Data':
            nova_data = st.date_input('Nova Data da reserva', format='DD/MM/YYYY')
            if st.button('Atualizar Reserva'):
                mydb.connect()

                if opcoes == 'Editar Reserva':
                    cursor.execute(f"UPDATE reserva SET data = '{nova_data}' WHERE id_cliente = {id_cliente}")
                    st.success('Reserva Atualizada')
                else:
                    cursor.execute(f"UPDATE reserva SET data = '{nova_data}' WHERE id_titular = {id_cliente}")
                    st.success('Reserva do Grupo Atualizada')
                mydb.close()

        if escolha_editar == 'Nome':

            nome_novo = st.text_input('Nome do Cliente', value=selectbox_cliente)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(f"UPDATE cliente SET nome = '{nome_novo}' WHERE id = {id_cliente}")
                mydb.close()
                st.success('Reserva Atualizada')

        if escolha_editar == 'CPF e Telefone':
            cpf_novo = st.text_input('Cpf do Cliente', value=cpf_cliente)
            telefone_novo = st.text_input('Telefone do Cliente', value=telefone_cliente)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE cliente SET cpf = '{cpf_novo}', telefone = '{telefone_novo}' WHERE id = {id_cliente}")
                mydb.close()
                st.success('Reserva Atualizada')

        if escolha_editar == 'Vendedor':
            mydb.connect()
            lista_vendedor = select_apelido_vendedores()

            cursor.execute(f"SELECT apelido FROM vendedores WHERE id = '{info_reserva[5]}'")
            comissario_antigo = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
            st.subheader(f'Vendedor : {comissario_antigo}')
            comissario_novo = st.selectbox('Selecione o novo vendedor', lista_vendedor, index=None)
            if st.button('Atualizar Reserva'):
                id_vendedor_editar = select_id_vendedores(comissario=comissario_novo)

                cursor.execute(
                    f"UPDATE reserva SET id_vendedor = '{id_vendedor_editar}' WHERE id_cliente = {id_cliente}")
                mydb.close()
                st.success('Reserva Atualizada')

        if escolha_editar == 'Certificação':
            st.subheader(f'Certificação: {info_reserva[2]}')
            tipo_novo = st.selectbox('Nova Certificação', ['BAT', 'TUR1', 'TUR2', 'OWD', 'ADV'], index=None)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE reserva SET tipo = '{tipo_novo}' WHERE id_cliente = {id_cliente}")
                mydb.close()
                st.success('Reserva Atualizada')
        if escolha_editar == 'Peso e Altura':
            roupa_novo = st.text_input('Peso do Cliente', value=roupa_cliente)
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE cliente SET roupa = '{roupa_novo}' WHERE id = {id_cliente}")
                mydb.close()
                st.success('Reserva Atualizada')

    st.write('---')
    if 'botao_vaga' not in st.session_state:
        st.session_state.botao_vaga = False

    if 'lista_id_vaga' not in st.session_state:
        st.session_state.lista_id_vaga = []

    if 'reserva_vaga' not in st.session_state:
        st.session_state.reserva_temporaria = []

    st.subheader('Dados Vagas Reservadas')
    lista_vendedores = select_apelido_vendedores()
    data_vaga = st.date_input('Data da  vaga reservada', format='DD/MM/YYYY')
    comissario_vaga = st.selectbox('Escolha o vendedor', lista_vendedores, index=None)

    if st.button('Pesquisar Vaga'):
        mydb.connect()
        nome_vaga = f'{data_vaga}/{comissario_vaga}'
        id_cliente_vaga = select_id_cliente_like(nome_vaga)
        if id_cliente_vaga:
            for id_ in id_cliente_vaga:
                st.session_state.lista_id_vaga.append(str(id_).translate(str.maketrans('', '', chars)))
            st.session_state.botao_vaga = True
        else:
            st.error('Nenhuma vaga reservada para esse comissario na data informada!')

    if st.session_state.botao_vaga:

        for i in range(len(st.session_state.lista_id_vaga)):
            with st.form(f'Vaga {comissario_vaga}-{i}'):
                st.subheader(f'Vaga Reservada {i + 1}')

                col1, col2, col3 = st.columns(3)
                with col1:
                    nome_cliente_vaga = st.text_input('Nome')
                    tipo = st.selectbox('Certificação', ['BAT', 'ACP', 'TUR1', 'TUR2', 'OWD', 'ADV'], index=None)
                    valor_vaga = st.text_input('Valor Total da reserva')
                    receber_vaga = st.text_input('Receber na Loja')
                with col2:
                    cpf_vaga = st.text_input('CPF')
                    peso_vaga = st.slider('Peso', 40, 160)
                    sinal_vaga = st.text_input('Valor pago de sinal')

                with col3:
                    telefone_vaga = st.text_input('Telefone')
                    altura_vaga = st.slider('Altura', 1.50, 2.20)
                    recebedor_sinal_vaga = st.selectbox('Recebedor do Sinal', ['Vendedor', 'AcquaWorld'], index=None)

                if st.form_submit_button(f'Cadastrar Cliente{i}'):
                    st.write(st.session_state.reserva_temporaria)
                    st.session_state.reserva_temporaria.append((st.session_state.lista_id_vaga[i], nome_cliente_vaga,
                                                                cpf_vaga, telefone_vaga, tipo, peso_vaga, altura_vaga,
                                                                valor_vaga, sinal_vaga, recebedor_sinal_vaga,
                                                                receber_vaga, data_vaga))
                    st.write(st.session_state.lista_id_vaga)

                    # st.session_state.lista_vaga.remove(st.session_state.lista_vaga[i])

        botao3 = st.button('Atualizar Reserva', key='reserva_vaga')

        if botao3:
            id_titular = st.session_state.lista_id_vaga[0]
            st.write(id_titular)
            id_vendedor_vaga = select_id_vendedores(comissario_vaga)
            for reserva in st.session_state.reserva_temporaria:
                update_vaga(reserva[0], reserva[1], reserva[2], reserva[3], reserva[4], reserva[5], reserva[6],
                            reserva[7], reserva[8], reserva[9], reserva[10], reserva[11], id_titular, id_vendedor_vaga)
            st.session_state.botao_vaga = False
            st.success('Reservas atualizadas com sucesso!')
            time.sleep(1.0)
            st.rerun()

if menu_main == 'Pagamento':
    # Iniciando variaveis e listas
    id_titular_pagamento = ''
    total_receber = 0

    if 'pagina_pagamento' not in st.session_state:
        st.session_state.pagina_pagamento = False

    if 'id_titular_pagamento' not in st.session_state:
        st.session_state.id_titular_pagamento = ''

    if 'nomes_cliente_pagamento' not in st.session_state:
        st.session_state.nomes_clientes_pagamento = []

    st.subheader('Pagamento')
    data_pagamento = st.date_input('Data da reserva')
    nome_titular_pagamento, nome_id_titular_pagamento = select_nome_id_titular(data_pagamento)
    select_box_titular = st.selectbox('Titular da Reserva', nome_titular_pagamento)
    if select_box_titular is None:
        st.warning('Nenhum lançamento para essa data')
        st.session_state.pagina_pagamento = False
    if st.button('Pesquisar reserva'):
        st.session_state.pagina_pagamento = True

    if st.session_state.pagina_pagamento:
        for dado in nome_id_titular_pagamento:
            if dado[0] == select_box_titular:
                st.session_state.id_titular_pagamento = dado[1]

        reservas_mesmo_nome = select_reserva_id_titular(st.session_state.id_titular_pagamento)

        titulo_tabela_pagamentos()  # Titulo da Tabela em HTML
        for clientes in reservas_mesmo_nome:

            id_reserva_pg, nome_cliente_pg, id_cliente_pg, tipo_pg, id_vendedor_pg, receber_loja, valor_total, situacao_pg, recebedor_pg, pagamento_pg = clientes

            if receber_loja is None:
                receber_loja = float(0.00)

            if receber_loja == pagamento_pg:
                receber_loja = float(0.00)

            if pagamento_pg:
                if pagamento_pg >= valor_total:
                    receber_loja = float(0.00)

            if situacao_pg is None:
                situacao_pg = 'Pendente'

            if recebedor_pg is None:
                texto_sinal = 'Nenhum sinal encontrado'

            else:
                texto_sinal = f'{recebedor_pg} - R$ {pagamento_pg}'

            coluna1, coluna2, coluna3, coluna4 = st.columns(4)

            with coluna1:
                st.markdown(
                    f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>{nome_cliente_pg}</h2>",
                    unsafe_allow_html=True)

            with coluna2:
                st.markdown(
                    f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>{texto_sinal}</h2>",
                    unsafe_allow_html=True)

            with coluna3:
                st.markdown(
                    f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>{format_currency(receber_loja, 'BRL', locale='pt_BR')}</h2>",
                    unsafe_allow_html=True)

            with coluna4:
                st.markdown(
                    f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>{situacao_pg}</h2>",
                    unsafe_allow_html=True)

            total_receber += float(receber_loja)

            st.session_state.nomes_clientes_pagamento.append(
                (nome_cliente_pg, id_cliente_pg, id_reserva_pg, receber_loja, id_vendedor_pg, tipo_pg, valor_total,
                 situacao_pg))

        nomes_pg = []
        nomes_pg_pendente = []
        for i in st.session_state.nomes_clientes_pagamento:
            if i[7] == 'Reserva Paga':
                nomes_pg.append(i[0])
            else:
                nomes_pg_pendente.append(i[0])

        if len(st.session_state.nomes_clientes_pagamento) == len(nomes_pg):
            st.success('Todos os clientes efetuaram o pagamento')

        else:
            if len(st.session_state.nomes_clientes_pagamento) < 1:
                pagamento_individual_coletivo = 'Pagamento em Grupo'
            else:
                pagamento_individual_coletivo = st.radio('Tipo de pagamento',
                                                         ['Pagamento Individual', 'Pagamento em Grupo'],
                                                         horizontal=True)

            if pagamento_individual_coletivo == 'Pagamento Individual':

                for i in st.session_state.nomes_clientes_pagamento:
                    if i[7] != 'Reserva Paga':
                        nomes_pg.append(i[0])

                select_box_cliente_pg = st.selectbox('Escolha o cliente', nomes_pg_pendente, index=None)

                for cliente in st.session_state.nomes_clientes_pagamento:
                    if select_box_cliente_pg == cliente[0]:
                        total_receber = cliente[3]

            total_receber_real = format_currency(total_receber, 'BRL', locale='pt_BR')
            valor_pago = st.text_input('Valor Pago', value=total_receber_real)

            forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                    index=None,
                                    placeholder='Insira a forma de pagamento')

            if forma_pg == 'Credito':
                parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)

            else:
                parcela = 0

            if forma_pg == 'Credito' or forma_pg == 'Debito':
                maquinas = select_maquina()
                maquina = st.selectbox('Maquininha', maquinas, index=None)

            else:
                maquina = ''

            check_in_entry = st.selectbox('Cliente vai pra onde?', ['Loja', 'Para o pier'], index=None)
            if check_in_entry == 'Loja':
                check_in = '#00B0F0'
            if check_in_entry == 'Para o pier':
                check_in = 'yellow'

            if st.button('Lançar Pagamento'):
                for reserva in st.session_state.nomes_clientes_pagamento:
                    if pagamento_individual_coletivo == 'Pagamento em Grupo':
                        if reserva[7] != 'Reserva Paga':
                            processar_pagamento(reserva[0], data_pagamento, check_in, forma_pg, parcela,
                                                reserva[4],
                                                st.session_state.id_titular_pagamento, reserva[2], reserva[1],
                                                reserva[5], reserva[6], total_receber, maquina)

                    else:
                        if select_box_cliente_pg == reserva[0]:
                            processar_pagamento(reserva[0], data_pagamento, check_in, forma_pg, parcela,
                                                reserva[4],
                                                st.session_state.id_titular_pagamento, reserva[2], reserva[1],
                                                reserva[5], reserva[6], total_receber, maquina)

                st.rerun()

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
