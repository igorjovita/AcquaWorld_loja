import streamlit as st
import base64


class Visualizar:

    def __init__(self, db, planilha):
        self.db = db
        self.planilha = planilha

    def tela_visualizar(self):


        # Função para obter cores com base no valor da coluna 'check_in'
        data = st.date_input("Data para gerar PDF:", format='DD/MM/YYYY')

        coluna1, coluna2 = st.columns(2)

        with coluna1:
            botao1 = st.button('Gerar Html')

        with coluna2:
            botao2 = st.button("Gerar PDF")

        if botao1:
            self.planilha.planilha_loja(data)

        if botao2:
            pdf_filename = self.planilha.planilha_barco(data)
            download_link = f'<a href="data:application/pdf;base64,{base64.b64encode(open(pdf_filename, "rb").read()).decode()}" download="{pdf_filename}">Clique aqui para baixar</a>'
            st.markdown(download_link, unsafe_allow_html=True)
