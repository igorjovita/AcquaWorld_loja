import streamlit as st
from streamlit_option_menu import option_menu
import base64
from functions import select_apelido_vendedores, select_nome_id_titular, calculo_restricao, gerar_pdf, gerar_html, \
    select_id_vendedores, insert_cliente, insert_reserva


def reserva():
    menu = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                       icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                       orientation='horizontal')

    if menu == 'Visualizar':  # PARTE OK
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

    if menu == 'Reservar':
        lista_nomes_clientes = []  # Lista para armazenar o nome dos clientes e itera-los posteriormente para acrescentar as demais informações

        if 'botao_clicado' not in st.session_state:  # Esse boolean que possibilita as inserções após pressionar um botão
            st.session_state.botao_clicado = False

        st.subheader('Reservar Cliente')

        lista_vendedor = select_apelido_vendedores()

        col1, col2, = st.columns(2)

        with col1:
            data = st.date_input('Data da Reserva', format='DD/MM/YYYY')
            comissario = st.selectbox('Vendedor:', lista_vendedor, index=None, placeholder='Escolha o vendedor')

        with col2:
            quantidade_reserva = st.number_input('Quantidade de Reservas', min_value=0, value=0, step=1)
            reserva_conjunta = st.selectbox('Agrupar reserva a Titular já reservado?', ['Sim', 'Não'], index=None)

        if reserva_conjunta == 'Sim':
            lista_titulares, _ = select_nome_id_titular(data)
            with col1:
                titular = st.selectbox('Escolha o titular', options=lista_titulares, index=None)
            if not titular:
                st.warning('Selecione o titular antes de adicionar clientes adicionais.')

        for i, in range(quantidade_reserva):
            nome_cliente = st.text_input(f'Nome do Cliente {i + 1}:').title()
            lista_nomes_clientes.append(nome_cliente)

        coluna1, coluna2 = st.columns(2)

        with coluna1:
            botao1 = st.button('Inserir dados do cliente')

        with coluna2:
            botao2 = st.button('Segurar vagas')

        if botao1:
            contagem, restricao, contagem_cred, vaga_bat, vaga_cred, vaga_total = calculo_restricao(data)

            if comissario is None:
                st.error('Insira o nome do comissario')
            elif contagem >= vaga_total:
                st.error('Planilha está lotada nessa data!')
            else:
                st.session_state.botao_clicado = True

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

        for i, nome_cliente in enumerate(lista_nomes_clientes):

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
