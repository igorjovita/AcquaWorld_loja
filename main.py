import base64

import pandas as pd
from babel.numbers import format_currency
from mysql.connector import IntegrityError
import streamlit as st
from streamlit_option_menu import option_menu
import os
import mysql.connector
from datetime import date
import streamlit.components.v1
from functions import select_reserva, processar_pagamento, gerar_pdf, gerar_html, select_apelido_vendedores, \
    calculo_restricao, insert_cliente, insert_reserva, select_id_vendedores, insert_lancamento_comissao, \
    select_valor_neto, select_cliente, select_grupo_reserva, update_vaga, select_id_cliente_like, \
    select_nome_id_titular, select_reserva_id_titular, titulo_tabela_pagamentos, select_pagamentos
import time

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
st.set_page_config(layout='wide', page_title='AcquaWorld', page_icon='🤿')

menu_main = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                        icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                        orientation='horizontal')

pasta = os.path.dirname(__file__)

if menu_main == 'Visualizar':
    # Função para obter cores com base no valor da coluna 'check_in'
    data_para_pdf = st.date_input("Data para gerar PDF:", format='DD/MM/YYYY')
    if st.button('Gerar Html'):
        tabela_html = gerar_html(data_para_pdf)
        st.components.v1.html(tabela_html, height=1000, width=1000, scrolling=True)
    st.write('---')

    # Formulário para gerar PDF

    if st.button("Gerar PDF"):
        pdf_filename = gerar_pdf(data_para_pdf)
        download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_filename, "rb").read()).decode()}" download="{pdf_filename}">Clique aqui para baixar</a>'
        st.markdown(download_link, unsafe_allow_html=True)

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
                                        ('BAT', 'ACP', 'TUR1', 'TUR2', 'OWD', 'ADV'),
                                        index=None, placeholder='Certificação', key=f'tipo{nome_cliente}{i}')
                    valor_mergulho = st.text_input(f'Valor do Mergulho',
                                                   key=f'valor{nome_cliente}{i}')
                    valor_loja = st.text_input(f'Valor a receber:', key=f'loja{nome_cliente}{i}')

                with st.expander('Data Pratica 2'):
                    data_pratica2 = st.date_input('Data da Pratica 2', format='DD/MM/YYYY', value=None)

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
                        if data_pratica2 is not None:
                            st.session_state.data_pratica2.append(data_pratica2)
                        else:
                            st.session_state.data_pratica2.append('')

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
            if st.session_state.data_pratica2:
                reservas.append(
                    (data, id_cliente, tipo, id_vendedor, valor_mergulho, nome_cliente, '#FFFFFF', id_titular,
                     valor_loja, st.session_state.data_pratica2[i]))
            st.write('---')

        if st.button('Reservar'):

            with mydb.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM reserva WHERE id_cliente = %s and data = %s",
                               (id_cliente, data))
                verifica_cpf = cursor.fetchone()[0]

                if verifica_cpf > 0:
                    st.error('Cliente já reservado para esta data')

                else:
                    for reserva in reservas:
                        id_reserva = insert_reserva(reserva)

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

    if 'botao' not in st.session_state:
        st.session_state.botao = False

    if 'id_pagamento' not in st.session_state:
        st.session_state.id_pagamento = []

    if 'id_pagamento' not in st.session_state:
        st.session_state.nome_id_pagamento = []

    if 'dados_pagamento' not in st.session_state:
        st.session_state.dados_pagamento = []

    if 'escolha_reserva_pendente' not in st.session_state:
        st.session_state.escolha_reserva_pendente = []

    data_pagamento = date.today()
    data_reserva = st.date_input('Data da reserva', format='DD/MM/YYYY')

    lista_pagamento = []

    lista_nome_id_titular = select_nome_id_titular(data_reserva)

    for dado in lista_nome_id_titular:
        lista_pagamento.append(str(dado[0]).translate(str.maketrans('', '', chars)))
        st.session_state.nome_id_pagamento.append(str(dado).translate(str.maketrans('', '', chars2)).split(','))

    if st.session_state.botao:
        selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista_pagamento, disabled=True)
    elif not st.session_state.botao:
        selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista_pagamento)

    c1, c2 = st.columns(2)
    with c1:
        if st.button('Selecionar Titular'):
            st.session_state.botao = True
            for nome, id_titular_pg in st.session_state.id_pagamento:
                if nome == selectbox_cliente:
                    st.session_state.id_pagamento.append(st.session_state.nome_id_pagamento)
                    id_titular_pagamento = id_titular_pg
            # st.rerun()
            st.write(st.session_state.id_pagamento)
    with c2:
        if st.button('Voltar'):
            st.session_state.botao = False
            st.rerun()

    if st.session_state.botao:
        dados_para_pagamento = []
        lista_nome_pagamento = []
        options_select_cliente = []
        escolha_reserva_pendente = []

        if selectbox_cliente is not None:

            for nome, id_titular_pg in st.session_state.id_pagamento:
                if nome == selectbox_cliente:
                    id_titular_pagamento = id_titular_pg
            st.session_state.id_pagamento = []

            dados_reservas_pagamento = select_reserva_id_titular(
                id_titular_pg)  # id, id_cliente, tipo, valor_total, receber_loja, id_vendedor
            id_vendedor_pg = dados_reservas_pagamento[0][4]

            for dado in dados_reservas_pagamento:
                id_reserva_pg, nome_reserva_pg, receber_loja_pg, situacao_reserva, id_vendedor, id_cliente_pg, tipo_pg, valor_total = dado

                dados_para_pagamento.append((nome_reserva_pg, id_reserva_pg, receber_loja_pg))

                if (nome_reserva_pg, situacao_reserva) not in options_select_cliente:
                    options_select_cliente.append((nome_reserva_pg, situacao_reserva))

                if (nome_reserva_pg, id_reserva_pg, id_cliente_pg, tipo_pg, valor_total, receber_loja_pg,
                    id_vendedor) not in st.session_state.dados_pagamento:
                    st.session_state.dados_pagamento.append(
                        (nome_reserva_pg, id_reserva_pg, id_cliente_pg, tipo_pg, valor_total, receber_loja_pg,
                         id_vendedor))
            receber_grupo = 0
            total_sinal = 0

            titulo_tabela_pagamentos()  # Titulo da Tabela em HTML

            for nome, id_pg, receber_loja in dados_para_pagamento:
                nome_formatado = str(nome).translate(str.maketrans('', '', chars))

                info_cliente_pg = select_reserva(nome=nome_formatado, data_reserva=data_reserva)

                if receber_loja is not None:
                    receber_formatado = float(str(receber_loja).translate(str.maketrans('', '', chars)))
                else:
                    receber_formatado = float(0.00)

                resultado_select_pagamentos = select_pagamentos(
                    int(str(id_pg).translate(str.maketrans('', '', chars))))

                if len(resultado_select_pagamentos) == 1:
                    recebedor, pagamento = resultado_select_pagamentos[0]  # Desempacotando a tupla

                elif len(resultado_select_pagamentos) > 1:
                    pagamento = 0
                    recebedor = resultado_select_pagamentos[0][0]  # Obtendo o recebedor da primeira tupla
                    for numero in resultado_select_pagamentos:
                        pagamento += numero[1]  # Somando os pagamentos das tuplas
                else:
                    recebedor = None

                lista_nome_pagamento.append(nome_formatado)

                coluna1, coluna2, coluna3, coluna4 = st.columns(4)

                with coluna1:
                    st.markdown(
                        f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>{nome_formatado}</h2>",
                        unsafe_allow_html=True)

                if recebedor is not None:
                    with coluna2:
                        pagamento_formatado = "{:,.2f}".format(pagamento).replace(",", "X").replace(".",
                                                                                                    ",").replace(
                            "X", ".")
                        st.markdown(
                            f"<h2 style='color: black; text-align: center; font-size: 1em;'>{recebedor} -  R$ {pagamento_formatado}</h2>",
                            unsafe_allow_html=True)
                    total_sinal += pagamento

                else:
                    with coluna2:
                        st.markdown(
                            f"<h2 style='color: black; text-align: center; font-size: 1em;'>Nenhum sinal foi pago</h2>",
                            unsafe_allow_html=True)
                        pagamento = 0

                with coluna3:
                    if info_cliente_pg[3] == pagamento:
                        receber_formatado_individual = 0.00
                        situacao = 'Pago'
                        pagamento = 0
                        receber_formatado = 0.00

                    else:
                        receber_formatado_individual = "{:,.2f}".format(receber_formatado).replace(",",
                                                                                                   "X").replace(
                            ".",
                            ",").replace(
                            "X", ".")
                        situacao = 'Pendente'
                    st.markdown(
                        f"<h2 style='color: black; text-align: center; font-size: 1em;'>R$ {receber_formatado_individual}</h2>",
                        unsafe_allow_html=True)

                receber_grupo += receber_formatado
                with coluna4:
                    st.markdown(
                        f"<h2 style='color: black; text-align: center; font-size: 1em;'>{situacao}</h2>",
                        unsafe_allow_html=True)

            if receber_grupo == 0.00:
                st.write('---')
                st.success('Todas os clientes dessa reserva efeturam o pagamento!')

            else:

                if len(lista_nome_pagamento) > 1:

                    colum1, colum2, colum3, colum4 = st.columns(4)

                    with colum1:
                        st.markdown(
                            f"<h2 style='color: black; text-align: center; font-size: 1.2em;'>Total</h2>",
                            unsafe_allow_html=True)

                    with colum2:
                        total_sinal_formatado = "{:,.2f}".format(total_sinal).replace(",", "X").replace(".",
                                                                                                        ",").replace(
                            "X", ".")
                        st.markdown(
                            f"<h2 style='color: green; text-align: center; font-size: 1.2em;'>R$ {total_sinal_formatado}</h2>",
                            unsafe_allow_html=True)

                    with colum3:
                        receber_grupo_formatado = "{:,.2f}".format(receber_grupo).replace(",", "X").replace(".",
                                                                                                            ",").replace(
                            "X", ".")
                        st.markdown(
                            f"<h2 style='color: green; text-align: center; font-size: 1.2em;'>R$ {receber_grupo_formatado}</h2>",
                            unsafe_allow_html=True)

                    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

                    pagamento_escolha = st.radio('Opções de pagamento',
                                                 ['Pagamento Grupo', 'Pagamento Individual'],
                                                 horizontal=True)

                else:
                    pagamento_escolha = 'Pagamento Individual'

                for opcao in options_select_cliente:
                    if opcao[1] == 'Reserva Paga':
                        pass
                    else:
                        if opcao[0] not in st.session_state.escolha_reserva_pendente:
                            st.session_state.escolha_reserva_pendente.append(opcao[0])

                if pagamento_escolha == 'Pagamento Individual':

                    escolha_client_input = st.selectbox('Cliente',
                                                        options=st.session_state.escolha_reserva_pendente)
                    st.write('---')

                    valor_a_receber_cliente = None
                    for nome, id_pg, receber_loja in dados_para_pagamento:
                        if nome == escolha_client_input:
                            valor_a_receber_cliente = receber_loja

                    if valor_a_receber_cliente is not None:
                        valor_a_receber_formatado = "{:,.2f}".format(valor_a_receber_cliente).replace(",",
                                                                                                      "X").replace(
                            ".", ",").replace("X", ".")
                        st.markdown(
                            f"<h2 style='color: green; font-size: 1.5em;'>Total a receber de {escolha_client_input} - R$ {valor_a_receber_formatado}</h2>",
                            unsafe_allow_html=True)
                    else:
                        st.warning(f"Não foi possível encontrar o valor a receber de {escolha_client_input}")

                    forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                            index=None,
                                            placeholder='Insira a forma de pagamento')

                    if forma_pg == 'Credito':
                        parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)
                    else:
                        parcela = 0

                    check_in_entry = st.selectbox('Cliente vai pra onde?', ['Loja', 'Para o pier'], index=None)
                    if check_in_entry == 'Loja':
                        check_in = '#00B0F0'
                    if check_in_entry == 'Para o pier':
                        check_in = 'yellow'
                    st.write(st.session_state.dados_pagamento)

                elif pagamento_escolha == 'Pagamento Grupo':
                    st.write('---')

                    st.subheader(f'Pagamento Grupo {selectbox_cliente}')
                    receber_grupo_formatado = "{:,.2f}".format(receber_grupo).replace(",", "X").replace(".",
                                                                                                        ",").replace(
                        "X", ".")
                    st.markdown(
                        f"<h2 style='color: green; font-size: 1.5em;'>Total a receber - R$ {receber_grupo_formatado}</h2>",
                        unsafe_allow_html=True)

                    forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                            index=None,
                                            placeholder='Insira a forma de pagamento')

                    if forma_pg == 'Credito':
                        parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)
                    else:
                        parcela = 0

                    check_in_entry = st.selectbox('Cliente vai pra onde?', ['Loja', 'Para o pier'], index=None)

                    if check_in_entry == 'Loja':
                        check_in = '#00B0F0'
                    if check_in_entry == 'Para o pier':
                        check_in = 'yellow'

                if st.button('Lançar Pagamento'):

                    if pagamento_escolha == 'Pagamento Grupo':

                        for dados_pagamento in st.session_state.dados_pagamento:
                            nome_cliente, id_reserva_pg, id_cliente_pg, tipo_pg, valor_total, receber_loja_pg, id_vendedor = dados_pagamento

                            if nome_cliente in st.session_state.escolha_reserva_pendente:
                                # Processa o pagamento apenas para o cliente selecionado
                                processar_pagamento(nome_cliente, data_reserva, check_in, forma_pg, parcela,
                                                    id_vendedor_pg,
                                                    id_titular_pagamento, id_reserva_pg, id_cliente_pg,
                                                    tipo_pg, valor_total, receber_loja_pg)

                    else:
                        for dados_pagamento in st.session_state.dados_pagamento:
                            nome_cliente, id_reserva_pg, id_cliente_pg, tipo_pg, valor_total, receber_loja_pg, id_vendedor = dados_pagamento

                            if nome_cliente == escolha_client_input:
                                id_reserva_selecionada = id_reserva_pg
                                id_cliente_selecionado = id_cliente_pg
                                tipo_selecionado = tipo_pg
                                valor_total_selecionado = valor_total
                                receber_loja_selecionado = receber_loja_pg
                        nome = escolha_client_input
                        processar_pagamento(nome, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg,
                                            id_titular_pagamento, id_reserva_selecionada, id_cliente_selecionado,
                                            tipo_selecionado, valor_total_selecionado, receber_loja_selecionado)
                    st.session_state.escolha_reserva_pendente.remove(nome)
                    st.session_state.pagamentos = []
                    st.session_state.pagamentos2 = []
                    st.session_state.dados_pagamento = []
                    st.session_state.escolha_reserva_pendente = []

                    time.sleep(0.5)
                    st.rerun()
                    mydb.close()
                    st.success('Pagamento lançado no sistema!')

                    st.session_state.botao = False

        else:
            st.warning('Nenhuma reserva lançada para essa data!')

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
