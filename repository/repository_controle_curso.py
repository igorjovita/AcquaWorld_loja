class RepositoryControleCurso:
    def __init__(self, db):
        self.db = db

    def select_controle_curso(self):
        query = """
        SELECT cliente.nome,
        c.data_pratica1,
        c.data_pratica2,
        cliente.telefone, 
        c.curso, 
        c.material, 
        c.situacao, 
        c.exercicios,
        c.certificacao 
        FROM controle_cursos as c 
        INNER JOIN cliente ON c.id_cliente = cliente.id"""

        return self.db.execute_query(query)

    def select_alunos_material_pendente(self):
        query = """
        SELECT cliente.id,
        cliente.nome 
        from controle_cursos as c 
        INNER JOIN cliente on c.id_cliente = cliente.id 
        WHERE (c.curso = 'OWD' or c.curso = 'ADV' or c.curso = 'RESCUE' or c.curso = 'EFR' or c.curso = 'DIVEMASTER') 
        and material = 'PENDENTE'"""

        return self.db.execute_query(query)

    def select_alunos_certificacao_pendente(self):
        query = """
        SELECT 
        cliente.id,
        cliente.nome,
        c.curso 
        from controle_cursos as c 
        INNER JOIN cliente on c.id_cliente = cliente.id 
        where c.certificacao = 'PENDENTE'
        """
        return self.db.execute_query(query)

    def select_contagem_pic_material_curso(self):
        query = """
         SELECT
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN pic_dive ELSE -pic_dive END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN pic_efr ELSE -pic_efr END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN open_pt ELSE -open_pt END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN open_es ELSE -open_es END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN open_ing ELSE -open_ing END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN adv ELSE -adv END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN efr ELSE -efr END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN rescue ELSE -rescue END),
            SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN dm ELSE -dm END) 
            FROM contagem_curso
        """

        return self.db.execute_query(query)

    def inserir_contagem_curso(self, data, tipo_movimento, pic_dive=None, pic_efr=None, open_pt=None, open_es=None,
                               open_ing=None, adv=None, efr=None, rescue=None, dm=None, emprestado=None):

        params = (data, tipo_movimento, pic_dive, pic_efr, open_pt, open_es, open_ing, adv, efr, rescue, dm, emprestado)

        query = """
        INSERT INTO contagem_curso 
        (data, tipo_movimento, pic_dive, pic_efr, open_pt, open_es, open_ing, adv, efr, rescue, dm, emprestado) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)

    def inserir_controle_curso(self, data_pratica1, data_pratica2, id_cliente, curso, material, situacao, exercicios,
                               certificacao):

        params = (data_pratica1, data_pratica2, id_cliente, curso, material, situacao, exercicios, certificacao)

        query = """
        INSERT INTO controle_cursos 
        (data_pratica1, data_pratica2, id_cliente, curso, material, situacao, exercicios, certificacao) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        # params = (data_pratica1, data_pratica2, id_cliente, tipo, 'PENDENTE', 'PENDENTE', 'PENDENTE', 'PENDENTE')

        return self.db.execute_query(query, params)

    def update_controle_curso_certificacao(self, n_certificacao, id_cliente, tipo, data):
        query = """
        UPDATE controle_cursos set certificacao = 'CERTIFICADO', exercicios = 'CONCLUIDO', n_certificacao = %s 
        WHERE id_cliente = %s"""
        params = (n_certificacao, id_cliente)
        self.db.execute_query(query, params)

        if tipo == 'EFR':
            self.inserir_contagem_curso(data, 'SAIDA', pic_efr=1)

        else:
            self.inserir_contagem_curso(data, 'SAIDA', pic_dive=1)

    def update_controle_curso_material(self, id_cliente):

        query = "UPDATE controle_cursos set material = 'ENTREGUE' where id_cliente = %s"

        params = (id_cliente,)

        return self.db.execute_query(query, params)


