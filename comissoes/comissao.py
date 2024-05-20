import pandas as pd
import streamlit as st
from babel.numbers import format_currency


class Comissao:

    def __init__(self, repository_vendedores, repository_pagamentos):
        self.repository_vedendores = repository_vendedores
        self.repository_pagamentos = repository_pagamentos

    def tela_comissao(self):
        total_pagar_somado = 0
        total_receber_somado = 0
        if 'tela_comissao' not in st.session_state:
            st.session_state.tela_comissao = False

        # Inicialize o estado (session state)
        state = st.session_state

        # Crie um DataFrame vazio para armazenar os dados
        if 'df_state' not in state:
            state.df_state = pd.DataFrame(
                columns=['Data', 'Titular', 'Tipo', 'Receber', 'Pagar', 'Pago na Loja', 'Situação'])
        lista_nomes_vendedores = []
        data1 = None
        data2 = None
        st.subheader('Comisão')
        select_id_apelido_vendedores = self.repository_vedendores.select_id_apelido()

        for resultado in select_id_apelido_vendedores:
            lista_nomes_vendedores.append(resultado[1])

        comissario = st.selectbox('Selecione o parceiro', options=lista_nomes_vendedores, index=None)
        situacao = st.selectbox('Situação do Pagamento', ['Pendente', 'Pago', 'Todos'], index=None,
                                placeholder='Selecione o status do pagamento')

        filtro = st.radio('Filtrar Pesquisa', options=['Todos os resultados', 'Data Especifica'])
        if filtro == 'Data Especifica':
            data1 = st.date_input('Data Inicial', format="DD/MM/YYYY")
            data2 = st.date_input('Data Final', format="DD/MM/YYYY")

        if st.button('Pesquisar Comissao'):
            st.session_state.tela_comissao = True

        if st.session_state.tela_comissao:
            if situacao == 'Todos':
                situacao = None
            tabela = []
            lista_id_nome_titular = []
            lista_nome_titular = []
            index = lista_nomes_vendedores.index(comissario)
            id_vendedor = select_id_apelido_vendedores[index][0]

            tabela_comissao = self.repository_vedendores.select_tabela_comissao(id_vendedor, data1, data2, situacao)

            # Suponha que resultado_select seja uma lista de tuplas (id, nome_prod, valor)
            for item in tabela_comissao:
                id_titular, data, titular, tipo, receber, pagar, pago_loja, situacao = item
                lista_id_nome_titular.append((id_titular, titular))
                tabela.append((data, titular, tipo, receber, pagar, pago_loja, situacao))
                lista_nome_titular.append(titular)

            df = pd.DataFrame(tabela,
                              columns=['Data', 'Titular', 'Tipo', 'Receber', 'Pagar', 'Pago na Loja', 'Situação'])

            df.insert(0, 'Selecionar', [False] * len(df))
            df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))
            soma_pagar_direta = df['Pagar'].sum()
            soma_receber_direta = df['Receber'].sum()
            df['Receber'] = df['Receber'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
            df['Pagar'] = df['Pagar'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))
            df['Pago na Loja'] = df['Pago na Loja'].map(lambda x: format_currency(x, 'BRL', locale='pt_BR'))

            # Armazenar o DataFrame no Session State
            state.df_state = df

            # Exibir DataFrame com st.data_editor
            state.df_state = st.data_editor(state.df_state, key="editable_df", hide_index=True, use_container_width=True)

            soma_receber_formatado = format_currency(float(soma_receber_direta), 'BRL', locale='pt_BR')
            soma_pagar_formatado = format_currency(float(soma_pagar_direta), 'BRL', locale='pt_BR')

            # Exibir totais abaixo do DataFrame
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"{comissario} pagar :")
                st.write(f'{soma_receber_formatado}')

            with col2:
                st.write(f"{comissario} receber:")
                st.write(f' {soma_pagar_formatado}')

            if len(st.session_state.df_state.loc[st.session_state.df_state['Selecionar']]) > 0:
                st.write('---')
                st.subheader('Acerto Comissão')
                # Calcule a soma dos valores dos itens selecionados
                total_pagar = st.session_state.df_state.loc[
                    st.session_state.df_state['Selecionar'], 'Pagar'].sum()
                total_receber = st.session_state.df_state.loc[
                    st.session_state.df_state['Selecionar'], 'Receber'].sum()

                lista_titular = st.session_state.df_state.loc[
                    st.session_state.df_state['Selecionar'], 'Titular'].tolist()

                lista_data = st.session_state.df_state.loc[
                    st.session_state.df_state['Selecionar'], 'Data'].tolist()

                total = str(total_pagar).replace('R$', '').replace('.', '').replace(',', '.').split()
                for valor in total:
                    total_pagar_somado += float(valor)

                total2 = str(total_receber).replace('R$', '').replace(',', '.').split()
                for valor2 in total2:
                    total_receber_somado += float(valor2)

                if total_pagar_somado > total_receber_somado:
                    pagamento = float(total_pagar_somado) - float(total_receber_somado)
                    recebedor = f'{comissario} receber :'
                else:
                    pagamento = float(total_receber_somado) - float(total_pagar_somado)
                    recebedor = f'{comissario} pagar :'

                pagamento_input = st.text_input(label=recebedor, value=pagamento)
                data_pagamento = st.date_input("Data do Pagamento", format='DD/MM/YYYY', key="data_pagamento")
                forma_pagamento = st.selectbox("Forma de Pagamento", options=['Pix', 'Dinheiro'], key="forma_pagamento",
                                               index=None)

                # Botão para lançar pagamento
                if st.button("Lançar Pagamento"):
                    for titular, data in zip(lista_titular, lista_data):
                        index = lista_nome_titular.index(titular)
                        id_titular_pagamento = lista_id_nome_titular[index][0]

                        st.write(id_titular_pagamento)
                        situacao = f'Pago dia {data}'
                        select_id_lancamento_comissao = self.repository_vedendores.select_id_lancamento_comissao(id_titular_pagamento)
                        for id_comissao in select_id_lancamento_comissao:

                            self.repository_vedendores.update_lancamento_comissao(situacao, id_comissao[0])

                        if recebedor == f'{comissario} pagar :':
                            self.repository_pagamentos.insert_caixa(1, data_pagamento, 'ENTRADA', 'ACERTO COMISSARIO', f'Acerto Vendedor {comissario}', forma_pagamento, pagamento_input)

                        else:
                            self.repository_pagamentos.insert_caixa(1, data_pagamento, 'SAIDA',
                                                                    'PGTO COMISSARIO',
                                                                    f'Pagamento Comissão {comissario}',
                                                                    forma_pagamento, pagamento_input)

                    st.session_state.tela_comissao = False
                    st.success('Dados alterados com sucesso!')