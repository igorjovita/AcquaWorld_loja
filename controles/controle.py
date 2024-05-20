import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import date
from babel.numbers import format_currency


class Controle:

    def __init__(self, repository_controle_curso, repository_pagamentos):
        self.repository_controle_curso = repository_controle_curso
        self.repository_pagamentos = repository_pagamentos

    def tela_controle(self):
        menu_controles = option_menu(menu_title="Controles", options=['Lançamentos', 'Cursos', 'Maquinas'],
                                     orientation='horizontal')

        if menu_controles == 'Lançamentos':
            st.subheader('Lançamentos')

            self.entrega_material()

            st.write('---')

            self.certificar()

            st.write('---')

            self.compra()

        if menu_controles == 'Cursos':

            st.subheader('Tabelas de controle')
            st.write('')
            st.write('')
            col1, col2, col3 = st.columns(3)

            with col1:
                botao_controle_curso = st.button('Abrir controle curso')

            with col2:
                botao_material_pic = st.button('Abrir controle material/pic')

            if botao_controle_curso:
                self.controle_curso()

            if botao_material_pic:
                self.controle_material_pic()

        if menu_controles == 'Maquinas':
            self.tela_maquinas()

    def entrega_material(self):

        with st.form('Entrega Material'):
            lista_alunos = []
            select_aluno_material_pendente = self.repository_controle_curso.select_alunos_material_pendente()

            for item in select_aluno_material_pendente:
                lista_alunos.append(item[1])

            materiais = ['OPEN - PT', 'OPEN - ES', 'OPEN - ING', 'AVANÇADO', 'EFR', 'RESCUE', 'DIVEMASTER']
            st.subheader('Entrega de material')
            aluno = st.selectbox('Escolha o aluno', options=lista_alunos, index=None)

            material = st.selectbox('Escolha o Material', options=materiais, index=None)

            with st.expander('Emprestar'):
                emprestado = st.text_input('Insira o nome de quem pegou emprestado').capitalize()

            if st.form_submit_button('Lançar no sistema'):
                curso_counts = {'OPEN - PT': 0, 'OPEN - ES': 0, 'OPEN - ING': 0, 'AVANÇADO': 0, 'EFR': 0, 'RESCUE': 0,
                                'DIVEMASTER': 0}

                index = lista_alunos.index(aluno)
                id_cliente = select_aluno_material_pendente[index][0]

                if material in curso_counts:
                    curso_counts[material] += 1

                data = date.today()

                self.repository_controle_curso.inserir_contagem_curso(data, 'SAIDA', '', '',
                                                                      open_pt=curso_counts['OPEN - PT'],
                                                                      open_es=curso_counts['OPEN - ES'],
                                                                      open_ing=curso_counts['OPEN - ING'],
                                                                      adv=curso_counts['AVANÇADO'],
                                                                      efr=curso_counts['EFR'],
                                                                      rescue=curso_counts['RESCUE'],
                                                                      dm=curso_counts['DIVEMASTER'],
                                                                      emprestado=emprestado)

                self.repository_controle_curso.update_controle_curso_material(id_cliente)

                st.success('Lançamento adicionado com sucesso!')

    def certificar(self):

        with st.form('Certificar'):
            lista_alunos = []
            select_aluno_cert_pendente = self.repository_controle_curso.select_alunos_certificacao_pendente()
            for item in select_aluno_cert_pendente:
                lista_alunos.append(item[1])

            st.subheader('Lançar certificaçao')

            aluno_certificar = st.selectbox('Alunos que foi certificado', lista_alunos, index=None)

            certificacao = st.text_input('Insira o numero da certificaçao')

            if st.form_submit_button('Lançar Certificaçao'):
                index = lista_alunos.index(aluno_certificar)
                id_cliente = select_aluno_cert_pendente[index][0]
                curso = select_aluno_cert_pendente[index][2]
                data = date.today()

                self.repository_controle_curso.update_controle_curso_certificacao(id_cliente, certificacao, curso, data)

                st.success('Sistema atualizado com sucesso!')

    def compra(self):

        with st.form('Compras'):
            st.subheader('Lançar Compra')

            col1, col2, col3 = st.columns(3)

            with col1:
                open_pt = st.text_input('Manual Open Water - Portugues')
                adv = st.text_input('Manual Avançado')
                dm = st.text_input('Manual DiveMaster')

            with col2:
                open_es = st.text_input('Manual Open Water - Espanhol')
                efr = st.text_input('Manual EFR')
                pic_dive = st.text_input('Pic Dive')
            with col3:
                open_ing = st.text_input('Manual Open Water - Inglês')
                rescue = st.text_input('Manual Rescue Diver')
                pic_efr = st.text_input('Pic EFR')

            with st.expander('Pegou emprestado?'):
                emprestado = st.text_input('Quem emprestou?').capitalize()
            if st.form_submit_button('Lançar'):
                data = date.today()
                tipo_movimento = 'ENTRADA'
                self.repository_controle_curso.inserir_contagem_curso(data, tipo_movimento, pic_dive, pic_efr, open_pt,
                                                                      open_es, open_ing, adv, efr, rescue,
                                                                      dm, emprestado)
                st.success('Lançamento cadastrado com sucesso')

    def controle_curso(self):
        select_controle_curso = self.repository_controle_curso.select_controle_curso()

        df = pd.DataFrame(select_controle_curso,
                          columns=['Cliente', 'Data Pratica 1', 'Data Pratica 2', 'Telefone', 'Curso', 'Material',
                                   'Situação', 'Exercicios', 'Certificação'])

        df['Data Pratica 1'] = df['Data Pratica 1'].apply(lambda x: x.strftime('%d/%m/%Y'))
        df['Data Pratica 2'] = df['Data Pratica 2'].apply(lambda x: x.strftime('%d/%m/%Y') if x else '')

        st.dataframe(df, hide_index=True, use_container_width=True)

    def controle_material_pic(self):
        select_material_pic = self.repository_controle_curso.select_contagem_pic_material_curso()

        df = pd.DataFrame(select_material_pic,
                          columns=['Pic Dive', 'Pic Efr', 'Open-PT', 'Open-ES', 'Open-ING', 'ADV', 'EFR',
                                   'Rescue',
                                   'DM'])
        st.dataframe(df, hide_index=True)

    def tela_maquinas(self):

        with st.form('Maquinas'):
            st.subheader('Controle Maquinas')
            lista_maquinas = []
            select_maquina_cartao = self.repository_pagamentos.select_maquina_cartao()
            for item in select_maquina_cartao:
                lista_maquinas.append(item)

            select_box_maquina = st.selectbox('Escolha a maquina para pesquisar', lista_maquinas, index=None)

            if st.form_submit_button('Pesquisar'):
                maquina_escolhida = self.repository_pagamentos.select_info_pagamento_por_maquina_cartao(
                    select_box_maquina)
                df = pd.DataFrame(maquina_escolhida,
                                  columns=['Data', 'Nome Cliente', 'Curso', 'Forma Pagamento', 'Parcela', 'Valor'])
                df['Data'] = df['Data'].apply(lambda x: x.strftime('%d/%m/%Y'))

                valor_total = format_currency(float(df['Valor'].sum()), 'BRL', locale='pt_BR')

                st.dataframe(df, hide_index=True, use_container_width=True)
                st.write(valor_total)
