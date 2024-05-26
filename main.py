import pandas as pd
import streamlit as st
from openpyxl import load_workbook

from tabelas import Planilhas
from database import DataBaseMysql
from repository import RepositoryVendedor, RepositoryReserva, RepositoryCliente, RepositoryControleCurso, \
    RepositoryPagamentos, RepositoryTermo

from excel import Excel

from streamlit_option_menu import option_menu

from reserva import Editar, Reserva, PagamentosPage, Visualizar
from caixa import Caixa
from comissoes import Comissao
from auth import Authentication
from cadastros import Cadastro
from controles import Controle
import os

from openpyxl import Workbook, load_workbook

st.set_page_config(layout="wide")
caminho_arquivo = r"C:\Users\Igorj\Downloads\MAIO 2024-teste.xlsx"
# Caminho do diretório a ser explorado
caminho_diretorio = r"C:\Users\Igorj\Downloads"

# Verificar se o caminho do diretório é válido
if os.path.exists(caminho_diretorio) and os.path.isdir(caminho_diretorio):
    # Listar os diretórios dentro do diretório especificado
    pastas = [pasta for pasta in os.listdir(caminho_diretorio) if os.path.isdir(os.path.join(caminho_diretorio, pasta))]

    # Exibir as pastas
    st.title("Pastas dentro de Downloads:")
    for pasta in pastas:
        st.write(pasta)
else:
    st.write("O caminho do diretório especificado não é válido.")


# caminho_arquivo_modelo = r"C:\Users\Igorj\Downloads\Modelo Planilha Operacao.xlsx"

auth = Authentication()
mysql = DataBaseMysql()
current_directory = os.getcwd()
caminho_arquivo_modelo = os.path.join(current_directory, "modelo.xlsx")
wb = load_workbook(r'/mount/src/acquaworld_loja/modelo.xlsx')
ws = wb.active


excel = 'oi'
# excel = Excel(caminho_arquivo, wb_modelo)
repository_vendedor = RepositoryVendedor(mysql)
repository_reserva = RepositoryReserva(mysql, excel)
repository_cliente = RepositoryCliente(mysql)
repositorio_curso = RepositoryControleCurso(mysql)
repository_pagamentos = RepositoryPagamentos(mysql)
repository_termo = RepositoryTermo(mysql)
pagamentos = PagamentosPage(repository_reserva, repository_pagamentos, repository_vendedor)

auth.authenticate()
auth.sidebar()

lista_nivel_1 = ['igorjovita']
escolha_pagina = None
if st.session_state["authentication_status"]:
    st.sidebar.write('---')
    st.sidebar.title('Menu')

    if st.session_state["username"] in lista_nivel_1:
        opcoes = ['📆 Reservas', '💰 Caixa', '📝 Termo', '🤝 Comissões', '📖 Controles', '📂 Cadastros', '📈 Financeiro']
    else:
        opcoes = ['📆 Reservas', '💰 Caixa', '📝 Termo', '🤝 Comissões', '📖 Controles', '📂 Cadastros']

    escolha_pagina = st.sidebar.radio('Opçoes', opcoes, label_visibility='collapsed', index=None)

if escolha_pagina == '📝 Termo':
    pass

if escolha_pagina == '🤝 Comissões':
    comissao = Comissao(repository_vendedor, repository_pagamentos)
    tela_comissao = comissao.tela_comissao()

if escolha_pagina == '💰 Caixa':
    caixa = Caixa(repository_pagamentos)
    tela_caixa = caixa.tela_caixa()

if escolha_pagina == '📖 Controles':
    controle = Controle(repositorio_curso, repository_pagamentos)
    controle.tela_controle()

if escolha_pagina == '📂 Cadastros':
    cadastro = Cadastro(repository_vendedor, repository_pagamentos)
    cadastro.tela_cadastro()

if escolha_pagina == '📆 Reservas':
    menu_reserva = option_menu(menu_title="Planilha Diaria", options=['Reservar', 'Visualizar', 'Editar', 'Pagamento'],
                               icons=['book', 'card-checklist', 'pencil-square', 'currency-dollar'],
                               orientation='horizontal')

    if menu_reserva == 'Reservar':
        reserva = Reserva(repository_vendedor, repository_reserva, repository_cliente, repository_pagamentos)
        reserva.tela_reserva()

    if menu_reserva == 'Pagamento':
        pagamentos.pagamentos()

    elif menu_reserva == 'Visualizar':
        planilha = Planilhas(repository_reserva)
        visualizar = Visualizar(mysql, planilha)
        visualizar.tela_visualizar()

    elif menu_reserva == 'Editar':
        editar = Editar(repository_reserva, repository_vendedor, repository_cliente)
        editar.tela_editar()
