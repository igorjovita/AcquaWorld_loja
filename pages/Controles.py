import streamlit as st
from streamlit_option_menu import option_menu

menu_controles = option_menu(menu_title="Controles", options=['Cursos', 'Maquinas'],
                        orientation='horizontal')

if menu_controles == 'Cursos':
    st.subheader('Controle de cursos')
