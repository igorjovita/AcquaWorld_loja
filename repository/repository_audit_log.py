

class RepositoryAuditLog:

    def __init__(self, db):
        self.db = db

    def select_logs_pendente_excel(self):

        query = "SELECT id, tipo, tabela , parametros FROM audit_log WHERE sincronizacao_excel = 'Pendente'"

        return self.db.execute_query(query)

    def select_logs_pendente_dropbox(self):
        query = "SELECT tipo, tabela , parametros FROM audit_log WHERE sincronizacao_dropbox = 'Pendente'"

        return self.db.execute_query(query)

    def updata_sincronizacao_excel(self, id):
        query = "UPDATE audit_log SET sincronizacao_excel = 'Sincronizado' WHERE id = %s"
        params = (id, )
        return self.db.execute_query(query, params)