import base64
import locale
import pdfkit
import jinja2
from babel.numbers import format_currency
from mysql.connector import IntegrityError
import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import os
import mysql.connector
from datetime import date, datetime
import streamlit.components.v1
from functions import obter_valor_neto, obter_info_reserva, update_check_in, insert_pagamento, calcular_valores,insert_lancamento_comissao, insert_caixa, processar_pagamento

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

escolha = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                      icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                      orientation='horizontal')

pasta = os.path.dirname(__file__)


# Inicializar listas


def gerar_pdf(self):
    mydb.connect()
    cliente = []
    cpf = []
    roupa = []
    cert = []
    foto = []
    dm = []
    background_colors = []
    # Consulta ao banco de dados para obter os dados
    cursor.execute(
        f"SELECT nome_cliente, tipo, fotos, dm, check_in FROM reserva WHERE data = '{data_para_pdf}'")
    lista_dados_reserva = cursor.fetchall()

    for dados in lista_dados_reserva:
        if dados[0] is None:
            cliente.append('')
        else:
            cliente.append(
                str(dados[0].encode('utf-8').decode('utf-8')).upper().translate(str.maketrans('', '', chars)))

        if dados[1] is None:
            cert.append('')
        else:
            cert.append(str(dados[1]).upper().translate(str.maketrans('', '', chars)))
        if dados[2] is None:
            foto.append('')
        else:
            foto.append(str(dados[2]).upper().translate(str.maketrans('', '', chars)))

        if dados[3] is None:
            dm.append('')
        else:
            dm.append(str(dados[3]).upper().translate(str.maketrans('', '', chars)))

        background_colors.append(str(dados[4]).translate(str.maketrans('', '', chars)))

    for nome in cliente:
        cursor.execute(
            f"SELECT cpf, roupa FROM cliente WHERE nome = '{nome}'")
        lista_dados_cliente = cursor.fetchall()

        for item in lista_dados_cliente:
            cpf.append(str(item[0]).translate(str.maketrans('', '', chars)))
            roupa.append(str(item[1]).translate(str.maketrans('', '', chars)))

    mydb.close()

    # Processar a data
    data_selecionada = str(data_para_pdf).split('-')
    dia, mes, ano = data_selecionada[2], data_selecionada[1], data_selecionada[0]
    data_completa = f'{dia}/{mes}/{ano}'

    # Criar o contexto
    contexto = {'cliente': cliente, 'cpf': cpf, 'c': cert, 'f': foto,
                'r': roupa, 'data_reserva': data_completa, 'background_colors': background_colors, 'dm': dm}

    # Renderizar o template HTML
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha.html')
    output_text = planilha.render(contexto)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_para_pdf}.pdf"

    # Gerar PDF
    config = pdfkit.configuration()
    options = {
        'encoding': 'utf-8',
        'no-images': None,
        'quiet': '',
    }
    pdfkit.from_string(output_text, pdf_filename, configuration=config, options=options)

    return pdf_filename


def gerar_html(self):
    mydb.connect()
    cliente = []
    cpf = []
    telefone = []
    roupa = []
    id_vendedor = []
    cert = []
    foto = []
    dm = []
    background_colors = []
    lista_id_vendedor = []
    comissario = []
    # Consulta ao banco de dados para obter os dados
    cursor.execute(
        f"SELECT nome_cliente,id_vendedor, tipo, fotos, dm, check_in FROM reserva WHERE data = '{data_para_pdf}'")
    lista_dados_reserva = cursor.fetchall()

    for dados in lista_dados_reserva:
        if dados[0] is None:
            cliente.append('')
        else:
            cliente.append(str(dados[0]).upper().translate(str.maketrans('', '', chars)))

        id_vendedor.append(str(dados[1]).translate(str.maketrans('', '', chars)))

        if dados[2] is None:
            cert.append('')
        else:
            cert.append(str(dados[2]).upper().translate(str.maketrans('', '', chars)))
        if dados[3] is None:
            foto.append('')
        else:
            foto.append(str(dados[3]).upper().translate(str.maketrans('', '', chars)))

        if dados[4] is None:
            dm.append('')
        else:
            dm.append(str(dados[4]).upper().translate(str.maketrans('', '', chars)))

        background_colors.append(str(dados[5]).translate(str.maketrans('', '', chars)))

    for nome in cliente:
        cursor.execute(
            f"SELECT cpf, telefone, roupa FROM cliente WHERE nome = '{nome}'")
        lista_dados_cliente = cursor.fetchall()

        for item in lista_dados_cliente:
            if item[0] is None:
                cpf.append('')
            else:
                cpf.append(str(item[0]).translate(str.maketrans('', '', chars)))

            if item[1] is None:
                telefone.append('')
            else:
                telefone.append(str(item[1]).translate(str.maketrans('', '', chars)))

            if item[2] is None:
                roupa.append('')
            else:
                roupa.append(str(item[2]).translate(str.maketrans('', '', chars)))

    for item in id_vendedor:
        lista_id_vendedor.append(str(item).translate(str.maketrans('', '', chars)))

    for id_v in lista_id_vendedor:
        cursor.execute(f"SELECT apelido from vendedores where id = '{id_v}'")
        comissario.append(str(cursor.fetchone()).upper().translate(str.maketrans('', '', chars)))

    mydb.close()

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
    planilha = planilha_env.get_template('planilha2.html')
    output_text = planilha.render(contexto)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_para_pdf}.pdf"

    # Gerar PDF
    config = pdfkit.configuration()
    pdfkit.from_string(output_text, pdf_filename, configuration=config)

    return output_text


if escolha == 'Visualizar':
    # Função para obter cores com base no valor da coluna 'check_in'
    data_para_pdf = st.date_input("Data para gerar PDF:")
    if st.button('Gerar Html'):
        tabela_html = gerar_html(data_para_pdf)
        st.components.v1.html(tabela_html, height=1000, width=1000, scrolling=True)
    st.write('---')

    # Formulário para gerar PDF

    if st.button("Gerar PDF"):
        pdf_filename = gerar_pdf(data_para_pdf)
        download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_filename, "rb").read()).decode()}" download="{pdf_filename}">Clique aqui para baixar</a>'
        st.markdown(download_link, unsafe_allow_html=True)

if escolha == 'Reservar':
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

    # Capturar nome dos vendedores cadastrados no sistema
    mydb.connect()
    cursor.execute("SELECT apelido FROM vendedores")
    lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

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
            nome_cliente = st.text_input(f'Nome do Cliente {i + 1}:').capitalize()
            nomes_clientes.append(nome_cliente)

    if st.button('Inserir dados do cliente'):
        st.session_state.botao_clicado = True

    if st.session_state.botao_clicado:
        with mydb.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM reserva where data = '{data}'")
            contagem = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

            cursor.execute(f"SELECT * FROM restricao WHERE data = '{data}'")
            restricao = cursor.fetchone()

            cursor.execute(
                f"SELECT COUNT(*) FROM reserva WHERE (tipo = 'TUR2' or tipo = 'OWD' or tipo = 'ADV' or tipo = "
                f"'RESCUE' or tipo = 'REVIEW') and data = '{data}'")
            contagem_cred = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

            lista_cred = ['TUR2', 'OWD', 'ADV', 'RESCUE', 'REVIEW']

            if restricao is None:
                vaga_cred = 8
                vaga_total = 40
                vaga_bat = vaga_total - contagem_cred
            else:
                cursor.execute(
                    f"SELECT vaga_bat, vaga_cred, vaga_total FROM restricao WHERE data = '{data}'")
                restricoes = str(cursor.fetchone()).translate(str.maketrans('', '', chars)).split()
                vaga_bat = int(restricoes[0])
                vaga_cred = int(restricoes[1])
                vaga_total = int(restricoes[2])

            if contagem >= vaga_total:
                st.error('Planilha está lotada nessa data!')

        if comissario is None:
            st.error('Insira o vendedor dessa reserva!')
        else:
            # Exibir os campos adicionais para cada reserva
            for i, nome_cliente in enumerate(nomes_clientes):

                if reserva_conjunta == 'Sim':
                    nome_titular = titular

                if i == 0 and reserva_conjunta == 'Não':
                    st.subheader(f'Reserva Titular: {nome_cliente}')
                    st.text('Para acessar essa reserva posteriormente use o nome do titular!')
                    nome_titular = nome_cliente
                else:
                    st.subheader(f'Reserva  Cliente: {nome_cliente}')

                colu1, colu2, colu3 = st.columns(3)

                with colu1:
                    cpf = st.text_input(f'Cpf', help='Apenas números',
                                        key=f'cpf{nome_cliente}{i}')
                    altura = st.slider(f'Altura', 1.50, 2.10,
                                       key=f'altura{nome_cliente}{i}')
                    sinal = st.text_input(f'Valor do Sinal', key=f'sinal{nome_cliente}{i}')

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

                    roupa = f'{altura}/{peso}'

                if st.button(f'Cadastrar {nome_cliente}', key=f'button{i}'):

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
                                cursor.execute(
                                    "INSERT INTO cliente (cpf, nome, telefone, roupa) VALUES (%s, %s, %s, %s)",
                                    (cpf, nome_cliente, telefone, roupa))
                                id_cliente = cursor.lastrowid
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
                    cursor.execute(f"SELECT id FROM vendedores WHERE nome = '{comissario}'")
                    id_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars))

                    if reserva_conjunta == 'Sim':

                        cursor.execute(f"SELECT id_cliente from reserva where nome_cliente = '{titular}'")
                        id_titular = cursor.fetchone()[0]

                    else:
                        if id_titular is None:
                            id_titular = id_cliente

                reservas.append(
                    (data, id_cliente, tipo, id_vendedor, valor_mergulho, nome_cliente, '#FFFFFF', id_titular,
                     valor_loja))
                st.write('---')

        if st.button('Reservar'):
            if tipo in lista_cred and contagem_cred >= vaga_cred:
                st.write(contagem_cred)
                st.write(vaga_cred)
                st.write(restricao)
                st.error('Todas as vagas de credenciados foram preenchidas')

            else:
                with mydb.cursor() as cursor:
                    cursor.execute(f"SELECT COUNT(*) FROM reserva WHERE id_cliente = %s and data = %s",
                                   (id_cliente, data))
                    verifica_cpf = cursor.fetchone()[0]

                    if verifica_cpf > 0:
                        st.error('Cliente já reservado para esta data')

                    else:
                        for reserva in reservas:
                            sql = (
                                "INSERT INTO reserva (data, id_cliente, tipo, id_vendedor, valor_total, nome_cliente, check_in, id_titular, receber_loja) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)")

                            # Executar a inserção de múltiplos valores
                            cursor.execute(sql, reserva)
                            id_reserva = cursor.lastrowid

                            st.session_state.pagamentos2.append((id_titular, id_reserva))

                        for i in range(len(st.session_state.pagamentos)):
                            st.session_state.pagamentos[i] = st.session_state.pagamentos[i] + st.session_state.pagamentos2[i]

                        if recebedor_sinal != '':
                            for pagamento in st.session_state.pagamentos:
                                cursor.execute(
                                    "INSERT INTO pagamentos (data, recebedor, pagamento, forma_pg, id_titular, id_reserva) VALUES (%s,%s, %s, %s, %s, %s)",
                                    pagamento)
                            st.session_state['ids_clientes'] = []

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
                        if recebedor_sinal == 'AcquaWorld':
                            cursor.execute(
                                "INSERT INTO caixa (data, tipo_movimento, descricao, forma_pg, valor) VALUES (%s, %s, %s, %s, %s)",
                                (data, 'ENTRADA', descricao, forma_pg, st.session_state.valor_sinal))

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
        cursor.execute(f"SELECT id, cpf, telefone, roupa FROM cliente WHERE nome = '{selectbox_cliente}'")
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
            roupa_novo = st.text_input('Peso do Cliente', value=int(info_cliente[3]))
            if st.button('Atualizar Reserva'):
                mydb.connect()
                cursor.execute(
                    f"UPDATE cliente SET roupa = '{roupa_novo}' WHERE id = '{info_cliente[0]}'")
                mydb.close()
                st.success('Reserva Atualizada')

if escolha == 'Pagamento':

    if 'botao' not in st.session_state:
        st.session_state.botao = False

    data_pagamento = date.today()
    data_reserva = st.date_input('Data da reserva', format='DD/MM/YYYY')

    lista_pagamento = []
    with mydb.cursor() as cursor:
        cursor.execute(f"SELECT id_cliente FROM reserva WHERE data = '{data_reserva}' and id_titular = id_cliente")
        id_cliente_pagamento = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()

        for item in id_cliente_pagamento:
            cursor.execute(f"SELECT nome FROM cliente WHERE id = '{item}'")
            nome_cliente_pagamento = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
            lista_pagamento.append(nome_cliente_pagamento)

    selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista_pagamento)

    if st.button('Selecionar Titular'):
        st.session_state.botao = True
    if st.session_state.botao:

        with mydb.cursor() as cursor:
            cursor.execute(f"SELECT id_cliente,id_vendedor from reserva where nome_cliente = '{selectbox_cliente}' and data = '{data_reserva}'")
            resultado2 = cursor.fetchone()
            if resultado2:
                id_titular_pagamento = resultado2[0]
                id_vendedor_pg = resultado2[1]
                st.write(id_titular_pagamento)

                cursor.execute(f'SELECT nome_cliente FROM reserva WHERE id_titular = {id_titular_pagamento}')
                resultado_individual = cursor.fetchall()
                lista_cliente = []
                if resultado_individual:
                    for item in resultado_individual:
                        item_formatado = str(item).translate(str.maketrans('', '', chars))
                        lista_cliente.append(item_formatado)

            lista_nome_pagamento = []
            nome_cliente_reserva = []
            id_cliente_reserva = []
            receber_loja_reserva = []
            mydb.connect()
            cursor = mydb.cursor(buffered=True)

            cursor.execute(
                f'SELECT id, nome_cliente, receber_loja from reserva where id_titular = {id_titular_pagamento}')
            resultado_pg = cursor.fetchall()
            for item in resultado_pg:
                id_reserva_pg, nome_reserva_pg, receber_loja_pg = item

                nome_cliente_reserva.append(nome_reserva_pg)
                id_cliente_reserva.append(id_reserva_pg)
                receber_loja_reserva.append(receber_loja_pg)
            receber_grupo = 0
            total_sinal = 0
            colun1, colun2, colun3, colun4 = st.columns(4)

            with colun1:
                st.markdown(
                    f"<h2 style='color: white; text-align: center; font-size: 1.5em; font-weight: bold;'>Nome do Cliente</h2>",
                    unsafe_allow_html=True)
            with colun2:
                st.markdown(
                    f"<h2 style='color: white; font-size: 1.5em; text-align: center; font-weight: bold;'>Sinal</h2>",
                    unsafe_allow_html=True)

            with colun3:
                st.markdown(
                    f"<h2 style='color: white; font-size: 1.5em; text-align: center; font-weight: bold;'>Valor a Receber</h2>",
                    unsafe_allow_html=True)
            with colun4:
                st.markdown(
                    f"<h2 style='color: white; font-size: 1.5em; text-align: center; font-weight: bold;'>Situação</h2>",
                    unsafe_allow_html=True)

            for nome, id_pg, receber_loja in zip(nome_cliente_reserva, id_cliente_reserva,
                                                 receber_loja_reserva):
                nome_formatado = str(nome).translate(str.maketrans('', '', chars))
                id_formatado = int(str(id_pg).translate(str.maketrans('', '', chars)))
                if receber_loja is not None:
                    receber_formatado = float(str(receber_loja).translate(str.maketrans('', '', chars)))
                else:
                    receber_formatado = float(0.00)
                cursor.execute(f"SELECT recebedor, pagamento FROM pagamentos WHERE id_reserva = {id_formatado}")
                result = cursor.fetchone()

                if result is not None:
                    recebedor = result[0]
                    pagamento = result[1]
                else:
                    recebedor = None
                lista_nome_pagamento.append(nome_formatado)
                coluna1, coluna2, coluna3, coluna4 = st.columns(4)

                with coluna1:
                    st.markdown(
                        f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>{nome_formatado}</h2>",
                        unsafe_allow_html=True)

                if recebedor is not None:
                    with coluna2:
                        pagamento_formatado = "{:,.2f}".format(pagamento).replace(",", "X").replace(".",
                                                                                                    ",").replace(
                            "X", ".")
                        st.markdown(
                            f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>{recebedor} -  R$ {pagamento_formatado}</h2>",
                            unsafe_allow_html=True)
                    total_sinal += pagamento

                else:
                    with coluna2:
                        st.markdown(
                            f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>Nenhum sinal foi pago</h2>",
                            unsafe_allow_html=True)
                with coluna3:
                    receber_formatado_individual = "{:,.2f}".format(receber_formatado).replace(",",
                                                                                               "X").replace(".",
                                                                                                            ",").replace(
                        "X", ".")
                    st.markdown(
                        f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>R$ {receber_formatado_individual}</h2>",
                        unsafe_allow_html=True)

                receber_grupo += receber_formatado
                with coluna4:
                    st.markdown(
                        f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>Pendente</h2>",
                        unsafe_allow_html=True)

            if len(lista_nome_pagamento) > 1:

                colum1, colum2, colum3, colum4 = st.columns(4)

                with colum1:
                    st.markdown(f"<h2 style='color: white; text-align: center; font-size: 1.2em;'>Total</h2>",
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

                pagamento_escolha = st.radio('Opções de pagamento', ['Pagamento Grupo', 'Pagamento Individual'],
                                             horizontal=True)

            else:
                pagamento_escolha = 'Pagamento Individual'

            if pagamento_escolha == 'Pagamento Individual':
                escolha_client_input = st.selectbox('Cliente', options=lista_cliente)
                st.write('---')

                valor_a_receber_cliente = None
                for nome, id_pg, receber_loja in zip(nome_cliente_reserva, id_cliente_reserva,
                                                     receber_loja_reserva):
                    if nome == escolha_client_input:
                        valor_a_receber_cliente = receber_loja

                if valor_a_receber_cliente is not None:
                    valor_a_receber_formatado = "{:,.2f}".format(valor_a_receber_cliente).replace(",",
                                                                                                  "X").replace(
                        ".", ",").replace("X", ".")
                    st.markdown(
                        f"<h2 style='color: green; font-size: 1.5em;'>Total a receber para {escolha_client_input} - R$ {valor_a_receber_formatado}</h2>",
                        unsafe_allow_html=True)
                else:
                    st.warning(f"Não foi possível encontrar o valor a receber para {escolha_client_input}")

                forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                        index=None,
                                        placeholder='Insira a forma de pagamento')

                if forma_pg == 'Credito':
                    parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)
                else:
                    parcela = 0

                pagamento = st.text_input('Valor pago')
                check_in_entry = st.selectbox('Cliente vai pra onde?', ['Loja', 'Para o pier'], index=None)
                if check_in_entry == 'Loja':
                    check_in = '#00B0F0'
                if check_in_entry == 'Para o pier':
                    check_in = 'yellow'

                # if st.button('Lançar Pagamento'):
                #
                #     info_reserva = obter_info_reserva(cursor, escolha_client_input, data_reserva)
                #
                #     update_check_in(cursor, escolha_client_input, check_in)
                #
                #     id_reserva_cliente = info_reserva[0]
                #     id_cliente_pg = info_reserva[1]
                #     tipo = info_reserva[2]
                #     valor_total_reserva = info_reserva[3]
                #     receber_loja_individual = info_reserva[4]
                #
                #     valor_neto = obter_valor_neto(cursor, tipo, valor_total_reserva, id_vendedor_pg)
                #
                #
                #
                #
                #     cursor.execute(
                #         "INSERT INTO pagamentos (data ,id_reserva, recebedor, pagamento, forma_pg, parcela, id_titular) VALUES (%s,%s, %s, %s, %s, %s, %s)",
                #         (
                #             data_pagamento, id_reserva_cliente, 'AcquaWorld', pagamento, forma_pg, parcela,
                #             id_titular_pagamento))
                #     id_pagamento = cursor.lastrowid
                #
                #     cursor.execute(
                #         f"SELECT recebedor, sum(pagamento) from pagamentos where id_reserva = {id_reserva_cliente} group by recebedor")
                #     resultado_soma = cursor.fetchall()
                #     st.write(resultado_soma)
                #
                #     vendedor_nome = None
                #     vendedor_valor = None
                #     acquaworld_nome = None
                #     acquaworld_valor = None
                #     for result in resultado_soma:
                #         nome_result = result[0]
                #         valor = result[1]
                #
                #         if nome_result == 'Vendedor':
                #             vendedor_nome = nome_result
                #             vendedor_valor = valor
                #
                #         elif nome_result == 'AcquaWorld':
                #             acquaworld_nome = nome_result
                #             acquaworld_valor = valor
                #
                #     st.write(vendedor_nome)
                #     st.write(vendedor_valor)
                #     st.write(acquaworld_nome)
                #     st.write(acquaworld_valor)
                #     st.write(f'id_titular = {id_titular_pagamento}')
                #     reserva_neto = valor_total_reserva - valor_neto
                #
                #     valor_receber, valor_pagar, situacao = obter_valor_neto(cursor, tipo, valor_total_reserva, id_vendedor_pg)
                #
                #     st.write(f'Pagar : {valor_pagar}')
                #     st.write(f'Receber : {valor_receber}')
                #     data_completa = str(data_reserva).split('-')
                #     descricao = f'{nome} do dia {data_completa[2]}/{data_completa[1]}/{data_completa[0]}'
                #     id_conta = 1
                #     tipo_movimento = 'Entrada'
                #
                #     insert_caixa(cursor, id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento)
                #
                #     cursor.execute(
                #         "INSERT INTO lancamento_comissao (id_reserva, id_vendedor, valor_receber, valor_pagar, "
                #         "situacao, id_titular) VALUES (%s, %s, %s, %s, %s, %s)",
                #         (id_reserva_cliente, id_vendedor_pg,
                #          valor_receber, valor_pagar, situacao, id_titular_pagamento))
                #
                #     mydb.close()
                #     st.success('Pagamento lançado no sistema!')
                #     st.session_state.botao = False

            if pagamento_escolha == 'Pagamento Grupo':
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
                        for nome in lista_nome_pagamento:
                            processar_pagamento(nome, cursor, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg, id_titular_pagamento)
                    else:
                        nome = escolha_client_input
                        processar_pagamento(nome, cursor, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg,
                                            id_titular_pagamento)

                        # info_reserva = obter_info_reserva(cursor, nome, data_reserva)
                        #
                        # update_check_in(cursor, nome, check_in)
                        #
                        # id_reserva_cliente = info_reserva[0]
                        # id_cliente_pg = info_reserva[1]
                        # tipo = info_reserva[2]
                        # valor_total_reserva = info_reserva[3]
                        # receber_loja_individual = info_reserva[4]
                        #
                        # pagamento = receber_loja_individual
                        # recebedor_pagamento = 'AcquaWorld'
                        #
                        # id_pagamento = insert_pagamento(cursor, data_pagamento, id_reserva_cliente, recebedor, pagamento, forma_pg, parcela, id_titular_pagamento)
                        #
                        # cursor.execute(
                        #     f"SELECT recebedor, sum(pagamento) from pagamentos where id_reserva = {id_reserva_cliente} group by recebedor")
                        # resultado_soma = cursor.fetchall()
                        # st.write(resultado_soma)
                        #
                        # vendedor_nome = None
                        # vendedor_valor = None
                        # acquaworld_nome = None
                        # acquaworld_valor = None
                        #
                        # valor_neto = obter_valor_neto(cursor, tipo, valor_total_reserva, id_vendedor_pg)
                        # reserva_neto = valor_total_reserva - valor_neto
                        #
                        # for result in resultado_soma:
                        #     nome_result = result[0]
                        #     valor = result[1]
                        #
                        #     if nome_result == 'Vendedor':
                        #         vendedor_nome = nome_result
                        #         vendedor_valor = valor
                        #
                        #     elif nome_result == 'AcquaWorld':
                        #         acquaworld_nome = nome_result
                        #         acquaworld_valor = valor
                        #
                        # valor_receber, valor_pagar, situacao = calcular_valores(valor_neto, acquaworld_valor, vendedor_valor, reserva_neto)
                        #
                        # data_completa = str(data_reserva).split('-')
                        # descricao = f'{nome} do dia {data_completa[2]}/{data_completa[1]}/{data_completa[0]}'
                        # tipo_movimento = 'Entrada'
                        # id_conta = 1
                        #
                        # insert_caixa(cursor, id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento)
                        #
                        # insert_lancamento_comissao(cursor, id_reserva_cliente, id_vendedor_pg, valor_receber, valor_pagar, situacao, id_titular_pagamento)

                    st.session_state.pagamentos = []
                    st.session_state.pagamentos2 = []

                    mydb.close()
                    st.success('Pagamento lançado no sistema!')
                    st.session_state.botao = False

                else:
                    st.success('Todos os clientes desse grupo já realizaram o pagamento!')
            else:
                st.error('Nenhuma reserva para essa data')
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

# sinal_loja = float(str(info_reserva_pg[2]).strip('Decimal'))
# sinal_vendedor = float(str(info_reserva_pg[3]).strip('Decimal'))
# total_mergulho = float(str(info_reserva_pg[5]).strip('Decimal'))
# st.write(sinal_loja)
# st.write(sinal_vendedor)
# st.write(float(pagamento))
# st.write(valor_neto)
# pagoloja = float(pagamento) + sinal_loja
#
# if pagoloja > valor_neto:
#     valor_receber = 0
#     valor_pagar = pagoloja - valor_neto
#
# if pagoloja == valor_neto and sinal_vendedor == total_mergulho - valor_neto:
#     valor_receber = 0
#     valor_pagar = 0
#
# if pagoloja == valor_neto and sinal_vendedor != total_mergulho - valor_neto:
#     valor_receber = 0
#     valor_pagar = sinal_vendedor - (total_mergulho - valor_neto)
#
# if pagoloja < valor_neto and sinal_vendedor == total_mergulho - valor_neto:
#     valor_receber = (float(pagamento) + sinal_loja) - valor_neto
#     valor_pagar = 0
#
# if pagoloja < valor_neto and sinal_vendedor != total_mergulho - valor_neto:
#     valor_receber = (float(pagamento) + sinal_loja) - valor_neto
#     valor_pagar = valor_receber + (-sinal_vendedor)
#
# st.write(f'Valor Receber - R$ {valor_receber}')
#
# st.write(f'Valor a pagar - R$ {valor_pagar}')
#
