import streamlit as st


class Editar:

    def __init__(self, repository_reserva, repository_vendedores, repository_cliente):

        self.repository_reserva = repository_reserva
        self.repository_vendedores = repository_vendedores
        self.repository_cliente = repository_cliente

    def tela_editar(self):

        if 'pagina_editar' not in st.session_state:
            st.session_state.pagina_editar = False

        data = st.date_input('Data da reserva', format="DD/MM/YYYY")

        select_info_reserva, select_id_apelido_vendedores, lista_nomes_clientes, lista_nomes_vendedores = self.buscar_info_editar(
            data)

        selectbox_cliente = st.selectbox('Escolha a reserva para editar', options=lista_nomes_clientes, index=None)

        if st.button('Pesquisar reserva'):
            st.session_state.pagina_editar = True

        if st.session_state.pagina_editar:

            data_reserva, id_cliente, nome_cliente, cpf, telefone, roupa, tipo, id_titular, vendedor, id_vendedor, valor_total, valor_receber, data_pratica2 = self.logica_editar(
                select_info_reserva, lista_nomes_clientes, selectbox_cliente)

            with st.form('Pagina Editar'):
                st.subheader(f'Informações  reserva de {nome_cliente}')

                col1, col2, col3 = st.columns(3)

                with col1:
                    novo_data_reserva = st.date_input('Insira a nova data para essa reserva', format="DD/MM/YYYY",
                                                      value=data_reserva)

                    novo_telefone = st.text_input('Telefone do cliente', value=telefone)

                    novo_roupa = st.text_input('Peso e altura do cliente', value=roupa)

                with col2:
                    novo_nome_cliente = st.text_input('Nome do cliente', value=nome_cliente)
                    novo_tipo = st.selectbox('Tipo do cliente',
                                             options=['BAT', 'ACP', 'TUR1', 'TUR2', 'OWD', 'ADV', 'RESCUE', 'DM'],
                                             index=None, placeholder=tipo)
                    novo_valor_total = st.text_input('Valor total da reserva', value=valor_total)

                with col3:
                    novo_cpf = st.text_input('CPF do cliente', value=cpf)
                    novo_vendedor = st.selectbox('Vendedor da Reserva', options=lista_nomes_vendedores,
                                                 placeholder=vendedor, index=None)

                    novo_valor_receber = st.text_input('Valor para receber da reserva', value=valor_receber)

                novo_data_pratica2 = data_pratica2
                if tipo == 'OWD' or tipo == 'ADV':
                    novo_data_pratica2 = st.date_input('Insira a nova data para pratica 2', format="DD/MM/YYYY",
                                                       value=data_pratica2)

                radio_alterar_grupo = st.radio('Alterar  data e vendedor de todas as reservas relacionadas?',
                                               options=['Sim', 'Não'],
                                               index=None, horizontal=True)

                if st.form_submit_button('Editar informações'):
                    self.condicionais_reserva(novo_vendedor, novo_tipo,
                                              novo_nome_cliente, novo_cpf, novo_telefone, novo_roupa,
                                              novo_data_reserva, novo_valor_total,
                                              novo_valor_receber, novo_data_pratica2, radio_alterar_grupo,
                                              lista_nomes_vendedores,
                                              select_id_apelido_vendedores, select_info_reserva, lista_nomes_clientes,
                                              selectbox_cliente)

    def buscar_info_editar(self, data):

        lista_nomes_vendedores = []
        lista_nomes_clientes = []

        select_info_reserva = self.repository_reserva.obter_nome_id_tipo_reserva_por_data(data)
        select_id_apelido_vendedores = self.repository_vendedores.select_id_apelido()

        for reserva in select_info_reserva:
            lista_nomes_clientes.append(reserva[2])

        for vendedor in select_id_apelido_vendedores:
            lista_nomes_vendedores.append(vendedor[1])

        return select_info_reserva, select_id_apelido_vendedores, lista_nomes_clientes, lista_nomes_vendedores

    def logica_editar(self, select_info_reserva, lista_nomes_clientes, selectbox_cliente):

        index_reserva = lista_nomes_clientes.index(selectbox_cliente)
        reserva_selecionada = select_info_reserva[index_reserva]

        data_reserva = reserva_selecionada[0]
        id_cliente = reserva_selecionada[1]
        nome_cliente = reserva_selecionada[2]
        cpf = reserva_selecionada[3]
        telefone = reserva_selecionada[4]
        roupa = reserva_selecionada[5]
        tipo = reserva_selecionada[6]
        id_tiular = reserva_selecionada[7]
        vendedor = reserva_selecionada[8]
        id_vendedor = reserva_selecionada[9]
        valor_total = reserva_selecionada[10]
        valor_receber = reserva_selecionada[11]
        data_pratica2 = reserva_selecionada[12]

        return data_reserva, id_cliente, nome_cliente, cpf, telefone, roupa, tipo, id_tiular, vendedor, id_vendedor, valor_total, valor_receber, data_pratica2

    def condicionais_reserva(self, novo_vendedor, novo_tipo,
                             novo_nome_cliente, novo_cpf, novo_telefone, novo_roupa,
                             novo_data_reserva, novo_valor_total,
                             novo_valor_receber, novo_data_pratica2, radio_alterar_grupo,
                             lista_nomes_vendedores,
                             select_id_apelido_vendedores, select_info_reserva, lista_nomes_clientes,
                             selectbox_cliente):

        data_reserva, id_cliente, nome_cliente, cpf, telefone, roupa, tipo, id_titular, vendedor, id_vendedor, valor_total, valor_receber, data_pratica2 = self.logica_editar(
            select_info_reserva, lista_nomes_clientes, selectbox_cliente)

        id_novo_vendedor = id_vendedor

        if novo_vendedor is not None:
            index_vendedor = lista_nomes_vendedores.index(novo_vendedor)
            vendedor_selecionado = select_id_apelido_vendedores[index_vendedor]
            id_novo_vendedor = vendedor_selecionado[0]

        if novo_vendedor is None:
            novo_vendedor = vendedor

        if novo_tipo is None:
            novo_tipo = tipo

        if nome_cliente != novo_nome_cliente or cpf != novo_cpf or telefone != novo_telefone or roupa != novo_roupa:
            estado = None
            pais = None
            self.repository_cliente.update_cliente(id_cliente, novo_nome_cliente, novo_telefone,
                                                   novo_cpf,
                                                   estado, pais, novo_roupa)

        if data_reserva != novo_data_reserva or tipo != novo_tipo or vendedor != novo_vendedor or valor_total != float(
                novo_valor_total) or valor_receber != float(novo_valor_receber) or data_pratica2 != novo_data_pratica2:

            if radio_alterar_grupo == 'Sim':
                self.repository_reserva.update_reserva_grupo_tela_editar(novo_data_reserva,
                                                                         id_novo_vendedor,
                                                                         id_titular)

            else:
                self.repository_reserva.update_reserva_tela_editar(novo_data_reserva, novo_tipo,
                                                                   id_novo_vendedor, novo_valor_total,
                                                                   novo_valor_receber, novo_data_pratica2,
                                                                   id_cliente)

        return st.success('Alterações feitas com sucesso!!')
