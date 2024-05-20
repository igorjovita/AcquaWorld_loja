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

            reserva_grupo = self.reserva.obter_info_reserva_pagamentos_por_id(id_titular)  # Consulta Tabela Pagamentos

            total_receber, reservas_pagas, reservas_pg_pendente = self.formatacao_dados_pagamento(id_titular)


            # Verificação se todos os clientes já pagaram
            if len(reserva_grupo) == len(reservas_pagas):
                st.success('Todos os clientes efetuaram o pagamento')

            else:
                # Verificação se tem apenas um cliente nesse grupo, se verdadeiro ele define o tipo de pg como
                # individual
                if len(reserva_grupo) == 1:
                    tipo_pagamento = 'Pagamento Individual'

                else:
                    tipo_pagamento = st.radio('Tipo do pagamento',
                                              ['Pagamento Individual', 'Pagamento em Grupo'], index=None)

                if tipo_pagamento == 'Pagamento Individual':
                    total_receber, escolha_cliente = self.pagamento_individual(reservas_pg_pendente, reserva_grupo)

                forma_pg, maquina, parcela, status = self.inputs_final_pagamentos(total_receber)

                if st.button('Lançar Pagamento'):

                    for reserva in reserva_grupo:
                        st.write(reserva)
                        situacao = reserva[7]
                        if tipo_pagamento == 'Pagamento em Grupo':
                            if situacao != 'Reserva Paga':
                                self.processar_pagamento_final(reserva, forma_pg, maquina, parcela, status,
                                                               data, total_receber)
                                st.success('Pagamento do grupo registrado com sucesso!')

                        else:
                            if escolha_cliente == reserva[0] and situacao != 'Reserva Paga':
                                self.processar_pagamento_final(reserva, forma_pg, maquina, parcela, status,
                                                               data, total_receber)

                                st.success('Pagamento registrado com sucesso!')

    def processar_pagamento_final(self, reserva, forma_pg, maquina, parcela, status, data, total_receber):


        st.write(reserva)
        nome_cliente, id_cliente, id_reserva, receber_loja, id_vendedor, tipo, valor_total, situacao, id_titular, recebedor = reserva

        # Metodo para atualizar a cor de fundo da planilha diaria

        self.reserva.update_cor_fundo_reserva(status, nome_cliente, data)

        valor_pagar, valor_receber, situacao = self.logica_valor_pagar_e_receber(tipo, forma_pg, id_vendedor,
                                                                                 valor_total, id_reserva)

        self.repository_vendedor.insert_lancamento_comissao(id_reserva, id_vendedor, valor_receber, valor_pagar,
                                                            id_titular, situacao)

        if receber_loja != 0.00:
            data_formatada = data.strftime("%d/%m/%Y")
            descricao = f'{nome_cliente} do dia {data_formatada}'
            tipo_movimento_caixa = 'ENTRADA'
            id_conta = 1

            self.repository_pagamento.insert_pagamentos(data, id_reserva, 'AcquaWorld', receber_loja, forma_pg, parcela,
                                                        id_titular, maquina, 'Pagamento')

            self.repository_pagamento.insert_caixa(id_conta, data, tipo_movimento_caixa, tipo, descricao, forma_pg,
                                                   receber_loja)

    def inputs_final_pagamentos(self, total_receber):

        parcela = 0
        maquina = ''

        total_receber_formatado = format_currency(total_receber, 'BRL', locale='pt_BR')

        st.text_input('Valor Pago', value=total_receber_formatado)

        forma_pg = st.selectbox('Forma de pagamento', ['Dinheiro', 'Pix', 'Debito', 'Credito'],
                                index=None)

        if forma_pg == 'Credito' or forma_pg == 'Debito':
            lista_maquinas = []
            select_maquinas = self.repository_pagamento.select_maquina_cartao()
            for resultado in select_maquinas:
                lista_maquinas.append(resultado[0])

            maquina = st.selectbox('Maquininha', lista_maquinas, index=None)

            if forma_pg == 'Credito':
                parcela = st.slider('Numero de Parcelas', min_value=1, max_value=6)

        status = st.selectbox('Cliente vai pra onde?', ['Chegou na Loja', 'Direto pro pier'], index=None)

        return forma_pg, maquina, parcela, status

    def formatacao_dados_pagamento(self, id_titular):

        select_tabela = self.reserva.obter_info_pagamento_para_tabela_pagamentos(id_titular)

        df = pandas.DataFrame(select_tabela,
                              columns=['Cliente', 'Tipo', 'Vendedor', 'Valor Total', 'Receber Loja', 'Sinal ',
                                       'Pagamento', 'Situacao'])

        total_receber = df['Receber Loja'].sum()
        reservas_pagas = df.loc[df['Situacao'] == 'Reserva Paga', 'Cliente'].tolist()
        reservas_pg_pendente = df.loc[df['Situacao'] == 'Pendente', 'Cliente'].tolist()

        st.data_editor(df, hide_index=True, use_container_width=True)

        return total_receber, reservas_pagas, reservas_pg_pendente

    def pagamento_individual(self, reservas_pg_pendente, reservas_pagamento):

        total_receber = 0
        escolha_cliente = st.selectbox('Escolha o cliente', reservas_pg_pendente)

        for reserva in reservas_pagamento:
            nome_cliente = reserva[0]
            receber_loja = reserva[3]

            if nome_cliente == escolha_cliente:
                total_receber = float(receber_loja)
                break

        return total_receber, escolha_cliente

    def logica_valor_pagar_e_receber(self, tipo, forma_pg, id_vendedor, valor_total, id_reserva):

        tipos = ['BAT', 'ACP', 'TUR1', 'TUR2']
        valor_neto = 0

        if tipo in tipos:

            select_valor_neto = self.repository_vendedor.select_valor_neto(id_vendedor)

            if tipo == 'BAT':
                if forma_pg == forma_pg == 'Credito' or forma_pg == 'Debito':
                    valor_neto = select_valor_neto[0][1]
                else:
                    valor_neto = select_valor_neto[0][0]

            elif tipo == 'ACP':
                valor_neto = select_valor_neto[0][2]

            elif tipo == 'TUR1':
                valor_neto = select_valor_neto[0][3]

            elif tipo == 'TUR2':
                valor_neto = select_valor_neto[0][4]

        else:
            comissao_curso = valor_total * 10 / 100
            valor_neto = valor_total - comissao_curso

        comissao_vendedor = valor_total - valor_neto

        select_valor_pago_recebedor = self.repository_pagamento.obter_valor_pago_por_idreserva(id_reserva)

        valor_pago_vendedor = 0
        valor_pago_acquaworld = 0

        for resultado in select_valor_pago_recebedor:
            if resultado[0] == 'AcquaWorld':
                valor_pago_acquaworld += float(resultado[1])
            else:
                valor_pago_vendedor += float(resultado[1])

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
            valor_pagar = valor_pago_acquaworld - valor_neto

        elif valor_pago_acquaworld == valor_neto:
            valor_receber = 0

            if valor_pago_vendedor == comissao_vendedor:
                valor_pagar = 0
                situacao = 'Pago'

            else:
                valor_pagar = comissao_vendedor - valor_pago_vendedor

        return valor_pagar, valor_receber, situacao
