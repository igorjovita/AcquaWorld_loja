import streamlit as st
from streamlit_option_menu import option_menu
from functions import select_controle_curso, insert_contagem_curso, select_alunos
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

    st.subheader('Entrega de Material')
    lista_nome_alunos, lista_alunos = select_alunos()

    select_box_aluno = st.selectbox('Escolha o aluno', options=lista_nome_alunos, index=None)

    st.write(lista_alunos)
    
    if st.button('Lançar no sistema'):
        for aluno in lista_alunos:
            if aluno[0] == select_box_aluno:
                st.write(aluno[1])

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
        insert_contagem_curso(data, tipo_movimento, pic_dive, pic_efr, open_pt, open_es, open_ing, adv, efr, rescue, dm, emprestado)
        st.success('Lançamento cadastrado com sucesso')







