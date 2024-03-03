import streamlit as st
from streamlit_option_menu import option_menu
from functions import select_controle_curso
import pandas as pd

menu_controles = option_menu(menu_title="Controles", options=['Cursos', 'Maquinas'],
                        orientation='horizontal')

if menu_controles == 'Cursos':
    st.subheader('Controle de cursos')

    alunos = 'oi'

    dados = select_controle_curso()

    st.table(dados)
