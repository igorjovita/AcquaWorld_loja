import streamlit as st


class Termo:

    def __init__(self, repository_termo):
        self.repository_termo = repository_termo



    def tela_termo(self):


        if 'pagina_termo' not in st.session_state:
            st.session_state.pagina_termo = False


        st.subheader('Termo Responsabilidade')

        data = st.date_input('Escolha a data', format='DD/MM/YYYY')

        if st.button('Pesquisar no sistema'):
            st.session_state.pagina_termo = True

        if st.session_state.pagina_termo:
            pass
