import streamlit as st
from streamlit_option_menu import option_menu
from functions import select_controle_curso, insert_contagem_curso, select_alunos, update_controle_curso_material, \
    select_quantidade_material, select_curso_certificar, update_controle_curso_certificar
import pandas as pd
from datetime import date

menu_controles = option_menu(menu_title="Controles", options=['Cursos', 'Maquinas'],
                             orientation='horizontal')

if menu_controles == 'Cursos':
    st.subheader('Controle de cursos')

    dados = select_controle_curso()

    st.table(dados)

    st.write('---')

    st.header('Controle de Materiais e Pics')

    contagem = select_quantidade_material()

    tabela = pd.DataFrame(contagem,
                          columns=['Pic Dive', 'Pic Efr', 'Open-PT', 'Open-ES', 'Open-ING', 'ADV', 'EFR', 'Rescue',
                                   'DM'])
    st.dataframe(tabela, hide_index=True)

    st.write('---')

    emprestado = ''

    st.subheader('Entrega de Material')
    lista_nome_alunos, lista_alunos = select_alunos()
    materiais = ['OPEN - PT', 'OPEN - ES', 'OPEN - ING', 'AVANÇADO', 'EFR', 'RESCUE', 'DIVEMASTER']

    select_box_aluno = st.selectbox('Escolha o aluno', options=lista_nome_alunos, index=None)

    select_box_curso = st.selectbox('Escolha o Material', options=materiais, index=None)

    with st.expander('Emprestar'):
        emprestado = st.text_input('Insira o nome de quem pegou emprestado').upper()

    if st.button('Lançar no sistema'):
        pic_dive = 0
        pic_efr = 0
        open_pt = 0
        open_es = 0
        open_ing = 0
        adv = 0
        efr = 0
        rescue = 0
        dm = 0
        emprestado = ''
        for aluno in lista_alunos:
            if aluno[0] == select_box_aluno:
                id_aluno = aluno[1]
        if select_box_curso == 'OPEN - PT':
            open_pt += 1

        elif select_box_curso == 'OPEN - ES':
            open_es += 1

        elif select_box_curso == 'OPEN - ING':
            open_select_box_curso
        elif select_box_curso == 'AVANÇADO':
            adv += 1

        elif select_box_curso == 'EFR':
            efr += 1

        elif select_box_curso == 'RESCUE':
            rescue += 1

        elif select_box_curso == 'DIVEMASTER':
            dm += 1

        st.write(select_box_curso)
        st.write(open_pt)
        data = date.today()
        insert_contagem_curso(data, 'SAIDA', '', '', open_pt=open_pt, open_es=open_es, open_ing=open_ing, adv=adv,
                              efr=efr, rescue=rescue, dm=dm, emprestado=emprestado)
        if select_box_aluno:
            update_controle_curso_material(id_aluno)
        st.success('Sistema Atulizado com sucesso')

    st.write('---')

    st.subheader('Certificar')
    lista_alunos_certificar, lista_id_certificar = select_curso_certificar()

    aluno_certificar = st.selectbox('Alunos para Certificar', lista_alunos_certificar, index=None)
    exercicios = st.selectbox('O aluno concluiu os exercicios?', ['Sim', 'Não'], index=None)
    certificacao = st.text_input('Insira o numero da certificaçao')

    if st.button('Lançar Certificaçao'):
        for id_certificar in lista_id_certificar:
            if id_certificar[0] == aluno_certificar:
                id_aluno_certificar = id_certificar[1]

        update_controle_curso_certificar(id_aluno_certificar, certificacao)

    st.write('---')

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
        emprestado = st.text_input('Quem emprestou?').upper()
    if st.button('Lançar'):
        data = date.today()
        tipo_movimento = 'ENTRADA'
        insert_contagem_curso(data, tipo_movimento, pic_dive, pic_efr, open_pt, open_es, open_ing, adv, efr, rescue, dm,
                              emprestado)
        st.success('Lançamento cadastrado com sucesso')
