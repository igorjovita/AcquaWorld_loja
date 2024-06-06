import babel
import pandas
import streamlit as st
from babel.numbers import format_currency
from datetime import datetime


class PagamentosPage:

    def __init__(self, reserva, repository_pagamento, repository_vendedor):
        self.reserva = reserva
        self.repository_pagamento = repository_pagamento
        self.repository_vendedor = repository_vendedor

    def pagamentos(self):

        # Inicialização dos SessionState

        if 'pagina' not in st.session_state:
            st.session_state.pagina = False

        if 'valor_pago' not in st.session_state:
            st.session_state.valor_pago = []

        data = st.date_input('Data da reserva', format='DD/MM/YYYY')

        select_info_titular = self.reserva.obter_info_titular_reserva_por_data(data)  # Consulta Tabela Reserva

        nome_titular = [item[0] for item in select_info_titular]  # Itera sobre a tupla de nome e id_cliente

        select_box_titular = st.selectbox('Titular da reserva', options=nome_titular)

        if select_box_titular is None:
            st.warning('Nenhuma reserva para data informada')

            st.session_state.pagina = False

            botao = st.button('Pesquisar Reserva', disabled=True)
        else:
            botao = st.button('Pesquisar Reserva')

        if botao:
            st.session_state.pagina = True
        if st.session_state.pagina:

            index = nome_titular.index(select_box_titular)
            id_titular = select_info_titular[index][1]

            reserva_grupo = self.reserva.obter_info_reserva_pagamentos_por_id(id_titular,
                                                                              data)  # Consulta Tabela Pagamentos

            total_receber, reservas_pagas, reservas_pg_pendente, quantidade_clientes, lista_pg_pendente = self.formatacao_dados_pagamento(
                id_titular, data)

            # Verificação se todos os clientes já pagaram

            if quantidade_clientes == len(reservas_pagas):
                st.success('Todos os clientes efetuaram o pagamento')

            else:
                nome_pagamento_pendente = []
                for cliente in lista_pg_pendente:
                    nome_pagamento_pendente.append(cliente[0])

                lista_nome_pg_pendente = st.multiselect('Escolha os clientes para lançar o pagamento',
                                                        nome_pagamento_pendente)
                total_receber = 0

                for resultado in lista_pg_pendente:
                    nome, valor = resultado

                    if nome in lista_nome_pg_pendente:
                        total_receber += valor

                if lista_nome_pg_pendente:
                    forma_pg, maquina, parcela, status, taxa_cartao, input_desconto, cliente_desconto = self.inputs_final_pagamentos(
                        lista_nome_pg_pendente, total_receber, reserva_grupo, data, lista_pg_pendente)

    def processar_pagamento_final(self, reserva, forma_pg, maquina, parcela, status, data, taxa_cartao, input_desconto,
                                  cliente_desconto, pagamento_vendedor, pago_na_loja, lista_pg_pendente):

        nome_cliente, id_cliente, id_reserva, receber_loja, id_vendedor, tipo, valor_total, situacao, recebedor, id_titular, total_pago, desconto = reserva

        pago_vendedor = 0
        for pagamento in pagamento_vendedor:

            if nome_cliente == pagamento[0]:
                pagamento_vendedor = pagamento_vendedor[0][1]
                pago_vendedor += float(pagamento_vendedor)
                self.repository_pagamento.insert_pagamentos(data, id_reserva, 'Vendedor', pagamento_vendedor,
                                                            'Pix', parcela, id_titular, maquina, 'Sinal', nome_cliente)

        desconto = float(desconto)

        valor_pago = float(receber_loja) + int(taxa_cartao) - float(desconto) - float(pago_vendedor)

        if input_desconto:

            if len(cliente_desconto) > 1:
                for cliente in cliente_desconto:
                    if cliente == nome_cliente:
                        desconto += float(input_desconto)
                        valor_pago -= float(input_desconto)
                        self.reserva.update_desconto_reserva(float(input_desconto) / len(cliente_desconto), id_reserva)

            elif len(cliente_desconto) == 1:
                if cliente_desconto[0] == nome_cliente:
                    desconto += float(input_desconto)
                    valor_pago -= float(input_desconto)
                    self.reserva.update_desconto_reserva(float(input_desconto), id_reserva)

        valor_pagar, valor_receber, situacao, valor_pago_acquaworld, valor_pago_vendedor = self.logica_valor_pagar_e_receber(
            tipo, forma_pg, id_vendedor,
            valor_total, id_reserva, valor_pago,
            desconto, taxa_cartao)

        st.write(f'Cliente - {nome_cliente}')
        st.write(f'Pago Acqua : {valor_pago_acquaworld}')
        st.write(f'Pago Vendedor : {valor_pago_vendedor}')
        st.write(f'Valor a pagar : {valor_pagar}')
        st.write(f'Valor Receber : {valor_receber}')
        st.write(f'Situação : {situacao}')

        if float(valor_pagar) != 0.00 or float(valor_receber) != 0.00:
            self.repository_vendedor.insert_lancamento_comissao(id_reserva, id_vendedor, valor_receber, valor_pagar,
                                                                id_titular, situacao)

        if tipo == 'OWD' or tipo == 'ADV':
            self.reserva.update_situacao_reserva(int(id_reserva) + 1)

        if float(valor_pago) != 0.00:
            self.repository_pagamento.insert_pagamentos(data, id_reserva, 'AcquaWorld', valor_pago, forma_pg, parcela,
                                                        id_titular, maquina, 'Pagamento', nome_cliente)

        self.reserva.update_cor_fundo_reserva(status, nome_cliente, data)

        return valor_pago

    def inputs_final_pagamentos(self, lista_nome_pg_pendente, total_receber, reserva_grupo, data, lista_pg_pendente):

        parcela = 0
        maquina = ''
        lista_maquinas = []
        forma_pg = ''
        input_desconto = None
        cliente_desconto = None
        quantidade = len(lista_nome_pg_pendente)

        select_maquinas = self.repository_pagamento.select_maquina_cartao()
        for resultado in select_maquinas:
            lista_maquinas.append(resultado[0])

        if quantidade >= 1:
            with st.form('Formulario'):
                lista_pendentes = ','.join(lista_nome_pg_pendente)
                st.subheader(f'Pagamento - {lista_pendentes}')
                col1, col2 = st.columns(2)
                with col1:
                    input_desconto = st.text_input('Desconto por parte da empresa', value=0)

                with col2:
                    if quantidade > 1:
                        cliente_desconto = st.multiselect('Quem vai receber o desconto?', lista_nome_pg_pendente)

                    else:
                        cliente_desconto = st.selectbox('Quem vai receber o desconto?', lista_nome_pg_pendente)

                forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                        index=None)

                colu1, colu2, colu3 = st.columns(3)

                with colu1:
                    maquina = st.selectbox('Maquininha', lista_maquinas, index=None)

                with colu2:
                    taxa_cartao = st.text_input('Taxa cartão ?', value=0)

                    total_receber = float(total_receber) + float(taxa_cartao)
                    taxa_cartao = int(taxa_cartao) / int(quantidade)

                with colu3:
                    parcela = st.selectbox('Numero de Parcelas', [1, 2, 3, 4, 5])

                for nome in lista_nome_pg_pendente:
                    pago_vendedor = st.text_input(f'Pago vendedor cliente {nome}', value=0, key=nome)

                pago_na_loja = float(total_receber) - float(input_desconto) - float(pago_vendedor)

                total_receber_formatado = format_currency(pago_na_loja, 'BRL', locale='pt_BR')

                st.text_input('Valor Pago', value=total_receber_formatado)

                status = st.selectbox('Cliente vai pra onde?', ['Chegou na Loja', 'Direto pro pier'], index=None)

                if st.form_submit_button('Lançar pagamento'):
                    pagamento_vendedor = []

                    for nome in lista_nome_pg_pendente:

                        if st.session_state[nome] != 0:
                            pagamento_vendedor.append((nome, st.session_state[nome]))

                    total_iteracao = len(reserva_grupo)
                    nomes_pagamento = []
                    valor_pago_total = 0
                    id_conta = 1
                    data_pagamento = datetime.today()
                    tipo_movimento_caixa = 'ENTRADA'
                    tipo = 'PAGAMENTO'

                    for i, reserva in enumerate(reserva_grupo):

                        nome = str(reserva[0])

                        if nome in lista_nome_pg_pendente:

                            certificacao = str(reserva[5])
                            nome_com_tipo = f'{nome} ({certificacao})'

                            nomes_pagamento.append(nome_com_tipo)

                            situacao = reserva[7]

                            if quantidade > 1:

                                if situacao != 'Reserva Paga':
                                    valor_pago = self.processar_pagamento_final(reserva, forma_pg, maquina, parcela,
                                                                                status,
                                                                                data, taxa_cartao, input_desconto,
                                                                                cliente_desconto, pagamento_vendedor,
                                                                                pago_na_loja, lista_pg_pendente)

                                    valor_pago_total += valor_pago

                                    if i == total_iteracao - 1:
                                        nomes = ','.join(nomes_pagamento)

                                        descricao = f'{nomes} do dia {data}'

                                        self.repository_pagamento.insert_caixa(id_conta, data_pagamento,
                                                                               tipo_movimento_caixa,
                                                                               tipo, descricao,
                                                                               forma_pg,
                                                                               valor_pago_total)
                                    st.success('Pagamento do grupo registrado com sucesso!')

                            else:
                                if situacao != 'Reserva Paga':
                                    if lista_nome_pg_pendente[0] == reserva[0]:
                                        valor_pago = self.processar_pagamento_final(reserva, forma_pg, maquina, parcela,
                                                                                    status,
                                                                                    data, taxa_cartao, input_desconto,
                                                                                    cliente_desconto,
                                                                                    pagamento_vendedor, pago_na_loja,
                                                                                    lista_pg_pendente)

                                        descricao = f'{nome} do dia {data}'

                                        self.repository_pagamento.insert_caixa(id_conta, data_pagamento,
                                                                               tipo_movimento_caixa,
                                                                               tipo, descricao,
                                                                               forma_pg,
                                                                               valor_pago)

                                    st.success('Pagamento registrado com sucesso!')

        return forma_pg, maquina, parcela, status, taxa_cartao, input_desconto, cliente_desconto

    def formatacao_dados_pagamento(self, id_titular, data):

        select_tabela = self.reserva.obter_info_pagamento_para_tabela_pagamentos(id_titular, data)

        df = pandas.DataFrame(select_tabela,
                              columns=['Cliente', 'Tipo', 'Vendedor', 'Valor Total', 'Receber Loja', 'Sinal ',
                                       'Pagamento', 'Situacao'])
        df_pendente = df.loc[df['Situacao'] == 'Pendente']
        total_receber = df_pendente['Receber Loja'].sum()
        reservas_pagas = df.loc[df['Situacao'] == 'Reserva Paga', 'Cliente'].tolist()
        reservas_pg_pendente = df.loc[df['Situacao'] == 'Pendente', ['Cliente', 'Receber Loja']]
        quantidade_clientes_mesma_reserva = len(df)
        lista_pg_pendente = reservas_pg_pendente.to_records(index=False).tolist()

        st.table(df)

        return total_receber, reservas_pagas, reservas_pg_pendente, quantidade_clientes_mesma_reserva, lista_pg_pendente

    def pagamento_individual(self, reservas_pg_pendente, reservas_pagamento):

        total_receber = 0
        if len(reservas_pagamento) > 1:
            escolha_cliente = st.selectbox('Escolha o cliente', reservas_pg_pendente)

            for reserva in reservas_pagamento:
                nome_cliente = reserva[0]
                receber_loja = reserva[3]

                if nome_cliente == escolha_cliente:
                    total_receber = float(receber_loja)
                    break

        else:
            escolha_cliente = reservas_pagamento[0][0]
            total_receber = float(reservas_pagamento[0][3])

        return total_receber, escolha_cliente

    def logica_valor_pagar_e_receber(self, tipo, forma_pg, id_vendedor, valor_total, id_reserva, pago_loja, desconto,
                                     taxa_cartao):

        tipos = ['BAT', 'ACP', 'TUR1', 'TUR2']
        valor_neto = 0

        if id_vendedor == 12:

            comissao_vendedor = float(valor_total) * 0.01
            valor_neto = float(valor_total) - float(comissao_vendedor) - float(desconto)

        else:

            if tipo in tipos:

                select_valor_neto = self.repository_vendedor.select_valor_neto(id_vendedor)
                neto_bat, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2 = select_valor_neto[0]

                if tipo == 'BAT':
                    if forma_pg == forma_pg == 'Credito' or forma_pg == 'Debito':
                        valor_neto = int(neto_bat_cartao) - float(desconto)
                    else:
                        valor_neto = int(neto_bat) - float(desconto)

                elif tipo == 'ACP':
                    valor_neto = int(neto_acp) - float(desconto)

                elif tipo == 'TUR1':
                    valor_neto = int(neto_tur1) - float(desconto)

                elif tipo == 'TUR2':
                    valor_neto = int(neto_tur2) - float(desconto)

            else:
                comissao_curso = float(valor_total) * 10 / 100
                valor_neto = float(valor_total) - float(comissao_curso) - float(desconto)

        select_valor_pago_recebedor = self.repository_pagamento.obter_valor_pago_por_idreserva(id_reserva)

        valor_pago_vendedor = 0
        valor_pago_acquaworld = float(pago_loja) - float()

        for resultado in select_valor_pago_recebedor:
            if resultado[0] == 'AcquaWorld':
                valor_pago_acquaworld += float(resultado[1])
            else:
                valor_pago_vendedor += float(resultado[1])

        comissao_vendedor = float(valor_pago_acquaworld) + float(valor_pago_vendedor) - valor_neto

        situacao = 'Pendente'
        valor_receber = 0
        valor_pagar = 0

        # Cenario onde o que foi pago pra AcquaWorld é menor que o valor neto
        if valor_pago_acquaworld < valor_neto:
            valor_receber = valor_neto - valor_pago_acquaworld
            valor_pagar = 0

        # Cenario onde o que foi pago pra AcquaWorld é maior que o valor neto
        elif valor_pago_acquaworld > valor_neto:
            valor_receber = 0
            valor_pagar = valor_pago_acquaworld - valor_neto - taxa_cartao

        elif valor_pago_acquaworld == valor_neto:
            valor_receber = 0

            if valor_pago_vendedor == comissao_vendedor:
                valor_pagar = 0
                situacao = 'Pago'

            else:
                valor_pagar = float(comissao_vendedor) - float(valor_pago_vendedor)

        return valor_pagar, valor_receber, situacao, valor_pago_acquaworld, valor_pago_vendedor
