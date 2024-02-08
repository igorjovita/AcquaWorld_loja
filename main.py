import base64
from babel.numbers import format_currency
from mysql.connector import IntegrityError
import streamlit as st
from streamlit_option_menu import option_menu
import os
import mysql.connector
from datetime import date
import streamlit.components.v1
from functions import obter_info_reserva, processar_pagamento, gerar_pdf, gerar_html, seleciona_vendedores, \
    calculo_restricao, insert_cliente, insert_reserva, seleciona_vendedores_apelido, insert_lancamento_comissao, \
    obter_valor_neto
import time
from memory_profiler import profile
import functions
import pages.Caixa, pages.Comissão


@profile()
def main():
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
        lista_vendedor = seleciona_vendedores()

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

        if st.button('Inserir dados do cliente'):
            st.session_state.botao_clicado = True

        if st.session_state.botao_clicado:

            contagem, restricao, contagem_cred, vaga_bat, vaga_cred, vaga_total = calculo_restricao(data)

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
                        if valor_loja == '':
                            valor_loja = 0.00
                        else:
                            valor_loja = valor_loja
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

                        id_vendedor = seleciona_vendedores_apelido(comissario)

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

                lista_cred = ['TUR2', 'OWD', 'ADV', 'RESCUE', 'REVIEW']

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
                                id_reserva = insert_reserva(reserva)

                                st.session_state.pagamentos2.append((id_titular, id_reserva))

                            for i in range(len(st.session_state.pagamentos)):
                                st.session_state.pagamentos[i] = st.session_state.pagamentos[i] + \
                                                                 st.session_state.pagamentos2[i]

                            if recebedor_sinal != '':

                                for pagamento in st.session_state.pagamentos:
                                    cursor.execute(
                                        "INSERT INTO pagamentos (data, recebedor, pagamento, forma_pg, id_titular, id_reserva) VALUES (%s,%s, %s, %s, %s, %s)",
                                        pagamento)
                                st.session_state['ids_clientes'] = []

                            if recebedor_sinal == 'Vendedor' and valor_mergulho == sinal:

                                valor_neto = obter_valor_neto(tipo, valor_total_reserva=valor_mergulho,
                                                              id_vendedor_pg=id_vendedor)

                                lista_ids = []
                                for tupla in st.session_state.pagamentos2:
                                    lista_ids.append(tupla[1])

                                for item in lista_ids:
                                    insert_lancamento_comissao(id_reserva_cliente=item, id_vendedor_pg=id_vendedor,
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
                lista_vendedor = seleciona_vendedores()

                cursor.execute(f"SELECT apelido FROM vendedores WHERE id = '{info_reserva[1]}'")
                comissario_antigo = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
                st.subheader(f'Vendedor : {comissario_antigo}')
                comissario_novo = st.selectbox('Selecione o novo vendedor', lista_vendedor)
                if st.button('Atualizar Reserva'):
                    id_vendedor_editar = seleciona_vendedores_apelido(comissario=comissario_novo)

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
            cursor.execute(
                f"SELECT nome_cliente FROM reserva WHERE data = '{data_reserva}' and id_titular = id_cliente")
            resultado_select = cursor.fetchall()

            for item in resultado_select:
                nome_cliente_pagamento = str(item).translate(str.maketrans('', '', chars))
                lista_pagamento.append(nome_cliente_pagamento)

        selectbox_cliente = st.selectbox('Selecione a reserva para editar', lista_pagamento)

        if st.button('Selecionar Titular'):
            st.session_state.botao = True
        if st.session_state.botao:
            lista_nome_pagamento = []
            nome_cliente_reserva = []
            id_cliente_reserva = []
            receber_loja_reserva = []
            options_select_cliente = []
            escolha_reserva_pendente = []

            with mydb.cursor() as cursor:
                resultado2 = obter_info_reserva(nome=selectbox_cliente, data_reserva=data_reserva)
                if resultado2:
                    id_reserva = resultado2[0]
                    id_titular_pagamento = resultado2[1]
                    tipo = resultado2[2]
                    valor_total = resultado2[3]
                    id_vendedor_pg = resultado2[5]
                    st.write(id_titular_pagamento)

                    cursor.execute(
                        f"SELECT id, nome_cliente, receber_loja, situacao from reserva where id_titular = {id_titular_pagamento}")
                    resultado_pg = cursor.fetchall()
                    for item in resultado_pg:
                        id_reserva_pg, nome_reserva_pg, receber_loja_pg, situacao_reserva = item

                        nome_cliente_reserva.append(nome_reserva_pg)
                        id_cliente_reserva.append(id_reserva_pg)
                        receber_loja_reserva.append(receber_loja_pg)
                        options_select_cliente.append((nome_reserva_pg, situacao_reserva))
                    receber_grupo = 0
                    total_sinal = 0
                    colun1, colun2, colun3, colun4 = st.columns(4)

                    with colun1:
                        st.markdown(
                            f"<h2 style='color: black; text-align: center; font-size: 1.5em; font-weight: bold;'>Nome</h2>",
                            unsafe_allow_html=True)
                    with colun2:
                        st.markdown(
                            f"<h2 style='color: black; font-size: 1.5em; text-align: center; font-weight: bold;'>Valor Pago</h2>",
                            unsafe_allow_html=True)

                    with colun3:
                        st.markdown(
                            f"<h2 style='color: black; font-size: 1.5em; text-align: center; font-weight: bold;'>Valor a Receber</h2>",
                            unsafe_allow_html=True)
                    with colun4:
                        st.markdown(
                            f"<h2 style='color: black; font-size: 1.5em; text-align: center; font-weight: bold;'>Situação</h2>",
                            unsafe_allow_html=True)

                    for nome, id_pg, receber_loja in zip(nome_cliente_reserva, id_cliente_reserva,
                                                         receber_loja_reserva):
                        nome_formatado = str(nome).translate(str.maketrans('', '', chars))
                        id_formatado = int(str(id_pg).translate(str.maketrans('', '', chars)))

                        info_cliente_pg = obter_info_reserva(nome=nome_formatado, data_reserva=data_reserva)

                        if receber_loja is not None:
                            receber_formatado = float(str(receber_loja).translate(str.maketrans('', '', chars)))
                        else:
                            receber_formatado = float(0.00)

                        cursor.execute(f"SELECT recebedor, pagamento FROM pagamentos WHERE id_reserva = {id_formatado}")
                        result = cursor.fetchall()

                        if len(result) == 1:
                            recebedor, pagamento = result[0]  # Desempacotando a tupla

                        elif len(result) > 1:
                            pagamento = 0
                            recebedor = result[0][0]  # Obtendo o recebedor da primeira tupla
                            for numero in result:
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

                        if pagamento_escolha == 'Pagamento Individual':

                            for opcao in options_select_cliente:
                                if opcao[1] == 'Reserva Paga':
                                    pass
                                else:
                                    escolha_reserva_pendente.append(opcao[0])
                            escolha_client_input = st.selectbox('Cliente', options=escolha_reserva_pendente)
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
                                for nome in lista_nome_pagamento:
                                    processar_pagamento(nome, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg,
                                                        id_titular_pagamento)
                            else:
                                nome = escolha_client_input
                                processar_pagamento(nome, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg,
                                                    id_titular_pagamento)

                            st.session_state.pagamentos = []
                            st.session_state.pagamentos2 = []
                            nome_cliente_reserva.remove(nome)
                            time.sleep(0.5)
                            st.rerun()
                            mydb.close()
                            st.success('Pagamento lançado no sistema!')

                            # st.session_state.botao = False

                else:
                    st.warning('Nenhuma reserva lançada para essa data!')
    pages.Comissão()


if __name__ == '__main__':
    main()

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
