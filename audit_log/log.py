import re
import json
import streamlit as st
from datetime import date, datetime


class AuditLog:

    def custom_serializer(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")

    def preparar_para_log(self, query, params):
        tipo = query.split()[0]
        dicionario = {}
        usuario = st.session_state["username"]
        log_params = ''
        tabela = ''

        if query.strip().startswith('INSERT'):

            pattern_insert = r"INSERT INTO (\w+)\s*\((.*?)\)\s*VALUES"
            match_insert = re.search(pattern_insert, query, re.DOTALL)

            if match_insert:
                tabela = match_insert.group(1)
                columns = match_insert.group(2).replace(" ", "").split(',')

                for column, param in zip(columns, params):
                    dicionario[column] = param

        elif query.strip().startswith('UPDATE'):

            update_pattern = r"UPDATE (\w+)\s+SET\s+(.*?)\s+WHERE\s+(.*)"

            update_match = re.search(update_pattern, query, re.DOTALL)
            if update_match:
                tabela = update_match.group(1)
                set_clause = update_match.group(2)
                where_clause = update_match.group(3)

                # Extraindo colunas da cláusula SET
                set_columns = [col.split('=')[0].strip() for col in set_clause.split(',')]
                where_columns = [col.strip().split(' ')[0] for col in where_clause.split('AND')]

                # Dividindo os parâmetros em SET e WHERE
                set_params = params[:len(set_columns)]
                where_params = params[len(set_columns):]

                # Criando o dicionário aninhado
                dicionario = {
                    'SET': {column: param for column, param in zip(set_columns, set_params)},
                    'WHERE': {column: param for column, param in zip(where_columns, where_params)}
                }

        elif query.strip().startswith('DELETE'):

            delete_pattern = r"DELETE FROM (\w+)\s*WHERE\s*(.*)"
            delete_match = re.search(delete_pattern, query, re.DOTALL)
            if delete_match:
                tabela = delete_match.group(1)
                where_clause = delete_match.group(2)

                # Extraindo colunas da cláusula WHERE
                columns = [col.strip().split(' ')[0] for col in where_clause.split('AND')]

                # Exemplo de dicionário de log de auditoria para DELETE
                dicionario = {
                    'WHERE': {column: param for column, param in zip(columns, params)}
                }

        dicionario = json.dumps(dicionario, default=self.custom_serializer, indent=4)

        log_params = (usuario, tipo, tabela, dicionario)

        log_query = 'INSERT INTO audit_log (usuario, tipo, tabela, parametros) VALUES (%s, %s, %s, %s)'
        return log_query, log_params
