import datetime

import streamlit as st
from babel.numbers import format_currency
from streamlit_option_menu import option_menu


class Reserva:

    def __init__(self, repository_vendedores, repository_reserva, repository_cliente, repository_pagamentos):
        self.repository_vendedores = repository_vendedores
        self.repository_reserva = repository_reserva
        self.repository_cliente = repository_cliente
        self.repository_pagamentos = repository_pagamentos

    def tela_reserva(self):

        lista_vendedores = []
        lista_titulares = []
        select_vendedores = self.repository_vendedores.select_id_apelido()
        nome_titular = None

        if 'info_mensagem' not in st.session_state:
            st.session_state.info_mensagem = []

        if 'tela_reserva' not in st.session_state:
            st.session_state.tela_reserva = False

        for resultado in select_vendedores:
            lista_vendedores.append(resultado[1])

        with st.form('Formulario Reserva'):

            st.subheader('Reservar Cliente')

            col1, col2, = st.columns(2)

            with col1:
                data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
                comissario = st.selectbox('Vendedor:', lista_vendedores, index=None, placeholder='Escolha o vendedor')

            with col2:
                quantidade_reserva = st.number_input('Quantidade de Reservas', min_value=0, value=0, step=1)
                reserva_conjunta = st.selectbox('Agrupar reserva a Titular já reservado?', ['Sim', 'Não'], index=None,
                                                key='reserva_conjunta')

            select_id_nome_titular = None

            if reserva_conjunta == 'Sim':
                select_id_nome_titular = self.repository_reserva.obter_info_titular_reserva_por_data(data)
                for cliente in select_id_nome_titular:
                    lista_titulares.append(cliente[0])

                with col1:
                    nome_titular = st.selectbox('Escolha o titular', options=lista_titulares, index=None)

            vaga_credenciado = 8
            id_titular = None
            id_vendedor = None

            if st.form_submit_button('Inserir Informações'):

                if 'id_vendedor' not in st.session_state:
                    st.session_state.id_vendedor = None

                if nome_titular is not None:
                    index_lista_titular = lista_titulares.index(nome_titular)
                    id_titular = select_id_nome_titular[index_lista_titular][0]

                index_lista_vendedor = lista_vendedores.index(comissario)
                st.session_state.id_vendedor = select_vendedores[index_lista_vendedor][0]

                vaga_credenciado, vaga_total = self.contagem_restricoes(data)

                reserva_pode_continuar = True

                if vaga_credenciado == 0:
                    st.warning('Não temos vagas para credenciados ou cursos')

                if vaga_total == 0:
                    st.warning('Planilha cheia')
                    reserva_pode_continuar = False

                if reserva_conjunta == 'Sim' and nome_titular is None:
                    st.warning('Informe o titular para realizar o agrupamento')
                    reserva_pode_continuar = False

                if comissario is None:
                    st.warning('O campo vendedor não pode ficar vazio')
                    reserva_pode_continuar = False

                if reserva_pode_continuar:
                    st.session_state.tela_reserva = True

        if st.session_state.tela_reserva:
            self.formulario_reserva(quantidade_reserva, data, vaga_credenciado, id_titular, nome_titular)

            if st.button('Gerar Mensagem '):
                self.mensagem_formatada(st.session_state.info_mensagem)

    def formulario_reserva(self, quantidade_reserva, data, vaga_credenciado, id_titular, nome_titular):
        nomes_dependentes = []

        soma_valor_total = 0
        soma_sinal = 0
        soma_receber_loja = 0

        with st.form(f'Formulario de reserva'):
            for i in range(int(quantidade_reserva)):
                print(i)

                if i == 0 and nome_titular is None:
                    st.subheader('Titular da reserva')

                else:
                    st.subheader('Reserva dependente')

                col1, col2, col3 = st.columns(3)

                with col1:
                    nome_cliente = st.text_input('Nome do cliente', key=f'nome {i}')
                    roupa = st.text_input(f'Peso e altura', key=f'roupa {i}')

                    sinal = st.text_input(f'Valor do Sinal', key=f'sinal {i}')

                with col2:
                    cpf = st.text_input('Cpf', key=f'cpf {i}')
                    tipo = st.selectbox(f'Certificação: ',
                                        ['BAT', 'ACP', 'TUR1', 'TUR2', 'OWD', 'ADV', 'EFR', 'RESCUE', 'DM'], index=None,
                                        key=f'tipo {i}')
                    recebedor_sinal = st.selectbox('Quem recebeu o sinal?', ['AcquaWorld', 'Vendedor'],
                                                   index=None, key=f'recebedor {i}')

                with col3:
                    telefone = st.text_input(f'Telefone:', key=f'telefone {i}')

                    valor_total = float(st.text_input(f'Valor do Mergulho', key=f'valor {i}', value=0))
                    receber_loja = float(st.text_input(f'Valor a receber:', key=f'loja {i}', value=0))

                desconto = st.text_input('Desconto Acqua')
                observacao = st.text_input('Observação', key=f'observacao {i}')

                with st.expander('Data Pratica 2'):
                    data_pratica2 = st.date_input('Data da Pratica 2', format='DD/MM/YYYY', value=None, key=f'data {i}')
                    if data_pratica2 == '0000-00-00':
                        data_pratica2 = ''

                st.write('---')

                if i != 0 or nome_titular is not None:
                    nomes_dependentes.append(nome_cliente)

                if i == 0 and nome_titular is None:
                    nome_titular = nome_cliente

            if st.form_submit_button('Reservar'):

                for i in range(int(quantidade_reserva)):
                    iteracao = i
                    nome_cliente = str(st.session_state[f'nome {i}']).title()
                    cpf = st.session_state[f'cpf {i}']
                    telefone = st.session_state[f'telefone {i}']
                    tipo = st.session_state[f'tipo {i}']
                    roupa = st.session_state[f'roupa {i}']
                    valor_total = st.session_state[f'valor {i}']
                    sinal = st.session_state[f'sinal {i}']
                    recebedor_sinal = st.session_state[f'recebedor {i}']
                    receber_loja = st.session_state[f'loja {i}']
                    observacao = st.session_state[f'observacao {i}']
                    soma_valor_total += int(valor_total)
                    soma_receber_loja += int(receber_loja)
                    if sinal != '':
                        soma_sinal += int(sinal)

                    if (tipo == 'OWD' or tipo == 'ADV') and data_pratica2 is None:
                        st.error('É necessario informar a data da pratica 2')

                    if sinal != '' and recebedor_sinal is None:
                        st.error('É necessario informar quem recebeu o sinal!')

                    else:
                        if cpf is None:
                            cpf = f'{nome_cliente} {data}'
                        self.reservar(data, nome_cliente, tipo, cpf, telefone, roupa, valor_total,
                                      sinal, recebedor_sinal, receber_loja, data_pratica2, id_titular, iteracao, observacao)

                st.session_state.info_mensagem.append(
                    (nome_titular, nomes_dependentes, soma_valor_total, soma_sinal, soma_receber_loja, data))

    def reservar(self, data, nome_cliente, tipo, cpf, telefone, roupa, valor_total, sinal,
                 recebedor_sinal, receber_loja, data_pratica2, id_titular, iteracao, observacao):

        if 'id_titular' not in st.session_state:
            st.session_state.id_titular = None

        observacao = str(observacao).upper()
        if cpf == '':
            cpf = f'{nome_cliente} {data}'

        id_cliente = self.repository_cliente.insert_cliente(nome_cliente, cpf, telefone, roupa)

        if id_titular is None and iteracao == 0:
            st.session_state.id_titular = id_cliente

        id_titular = st.session_state.id_titular
        id_vendedor = st.session_state.id_vendedor

        id_reserva = None
        if tipo == 'OWD' or tipo == 'ADV':
            for i in range(2):
                if i == 0:
                    id_reserva = self.repository_reserva.insert_reserva(data, id_cliente, tipo, id_vendedor,
                                                                        valor_total,
                                                                        (str(nome_cliente) + ' > PRÁTICA 1'),
                                                                        id_titular, receber_loja, observacao)

                else:
                    self.repository_reserva.insert_reserva(data_pratica2, id_cliente, tipo, id_vendedor, valor_total,
                                                           (str(nome_cliente) + ' > PRÁTICA 2'), id_titular,
                                                           float(0), observacao)
        else:
            id_reserva = self.repository_reserva.insert_reserva(data, id_cliente, tipo, id_vendedor, valor_total,
                                                                nome_cliente, id_titular, receber_loja, observacao)

        if sinal != '':
            self.repository_pagamentos.insert_pagamentos(data, id_reserva, recebedor_sinal, sinal, 'Pix', '',
                                                         id_titular, '',
                                                         'Sinal')

        if recebedor_sinal == 'AcquaWorld':
            data_pagamento = datetime.date.today()
            descricao = f'Sinal reserva {nome_cliente} do dia {data.strftime("%d/%m/%Y")}'
            self.repository_pagamentos.insert_caixa(1, data_pagamento, 'ENTRADA', 'SINAL', descricao, 'Pix', sinal)

        st.success(f'{nome_cliente} reservado com sucesso!')

        st.session_state.tela_reserva = False

    def mensagem_formatada(self, info):

        info = info[0]
        nome_titular = info[0]
        dependentes = info[1]
        valor_total = info[2]
        sinal = info[3]
        receber_loja = info[4]
        data = info = info[5]
        nomes_dependentes = ','.join(dependentes)

        mensagem = f"""
        *Reserva Concluida com Sucesso!*
    
Titular da Reserva - {nome_titular}"""

        if nomes_dependentes:
            mensagem += f"\nReservas Dependentes - {nomes_dependentes}"

        mensagem += f"""
    \nValor total - {format_currency(valor_total, 'BRL', locale='pt_BR')}
Já foi pago - {format_currency(sinal, 'BRL', locale='pt_BR')}
Falta pagar - {format_currency(receber_loja, 'BRL', locale='pt_BR')}


Favor chegar na data marcada: 

⚠️ {data.strftime("%d/%m/%Y")} às 07:30hs em nossa loja 

⚠️ Favor chegar na hora pois é necessário, efetuar o restante do pagamento caso ainda não tenha feito, preencher os termos de responsabilidade/questionário médico e fazer retirada da pulseirinha que dá acesso à embarcação.

⚓ O ponto de encontro será na loja de mergulho !⚓

➡️ARRAIAL DO CABO: Praça da Bandeira, n 23, Praia dos Anjos. Loja de Madeira na esquina, um pouco depois da rodoviária Indo pra praia dos anjos.

*Na Marina dos Anjos, a prefeitura cobra uma taxa de  embarque de R$ 10,00,  por pessoa em dinheiro.*
    """

        st.code(mensagem)
        st.session_state.info_mensagem = []

    def contagem_restricoes(self, data):

        select_contagem_reserva = self.repository_reserva.obter_contagem_reserva(data)
        contagem_reserva = select_contagem_reserva[0]

        total_curso_cred = contagem_reserva[8]
        total_reservas = contagem_reserva[9]

        contagem_restricao = self.repository_reserva.obter_contagem_restricao(data)
        print(contagem_restricao)
        print(total_curso_cred)
        print(total_reservas)

        if not contagem_restricao:
            vaga_credenciado = 8 - int(total_curso_cred)
            vaga_total = 40 - int(total_reservas)

        else:
            vaga_credenciado = int(contagem_restricao[0][1]) - int(total_curso_cred)
            vaga_total = int(contagem_restricao[0][2]) - int(total_reservas)

        print(vaga_credenciado)
        print(vaga_total)

        return vaga_credenciado, vaga_total
