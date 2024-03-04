import streamlit as st
from streamlit_option_menu import option_menu
from functions import select_controle_curso, insert_contagem_curso
import pandas as pd
from datetime import date

menu_controles = option_menu(menu_title="Controles", options=['Cursos', 'Maquinas'],
                        orientation='horizontal')

if menu_controles == 'Cursos':
    st.subheader('Controle de cursos')

    alunos = 'oi'

    dados = select_controle_curso()

    st.table(dados)

    st.write('---')

    st.header('Controle de Materiais e Pics')

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





