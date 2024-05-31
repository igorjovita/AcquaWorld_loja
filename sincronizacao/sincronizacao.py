import streamlit as st
import json


class Sincronizacao:

    def __init__(self, repository_audit_log):
        self.repository_audit_log = repository_audit_log


    # def tela_sincronizacao(self):
    #     st.subheader('Sincronização')
    #
    #     select_excel_pendente = self.repository_audit_log.select_logs_pendente_excel()
    #     quantidade_pendencias = len(select_excel_pendente)
    #     st.text(f'{quantidade_pendencias} Alterações não sincronizadas no armazenamento local')
    #
    #     if st.button('Sincronizar excel'):
    #         dicionario, dicionario_caixa = self.gerenciador_execel.controlador(select_excel_pendente)
    #         lista_ids_audit_log = None
    #         if dicionario_caixa:
    #             st.write('Dicionario Caixa')
    #             st.write(dicionario_caixa)
    #             lista_ids_audit_log = self.gerenciador_execel.insert_excel_caixa(dicionario_caixa)
    #
    #         if dicionario:
    #             lista_ids_audit_log = self.gerenciador_execel.insert_excel(dicionario)
    #
    #         if lista_ids_audit_log:
    #             for num_id in lista_ids_audit_log:
    #                 self.repository_audit_log.updata_sincronizacao_excel(num_id)
    #
    #         st.success('Dados Atualizados no armazenamento')