class RepositoryCliente:

    def __init__(self, db):
        self.db = db

    def obter_cpf_tel_roupa_cliente_por_id(self, id_cliente):
        params = (id_cliente,)

        query = """
        SELECT 
        CASE WHEN cpf IS NULL THEN '' ELSE cpf END, 
        CASE WHEN telefone IS NULL THEN '' ELSE telefone END, 
        CASE WHEN roupa IS NULL THEN '' ELSE roupa END 
        FROM cliente 
        WHERE id = %s"""

        return self.db.execute_query(query, params)

    def obter_id_cliente_por_nome_parecido(self, nome, data):
        params = (nome, data)

        query = "SELECT c.id FROM reserva as r INNER JOIN cliente as c on r.id_cliente = c.id where c.nome LIKE %s and r.data = %s"

        return self.db.execute_query(query, params)

    def insert_cliente(self, nome, cpf, telefone, roupa):
        params = (nome, cpf, telefone, roupa)

        query = "INSERT INTO cliente (nome, cpf,  telefone, roupa) VALUES (%s, %s, %s, %s)"

        return self.db.execute_query(query, params)

    def update_cliente(self, id_cliente, nome, telefone, cpf, estado, pais, roupa):
        if estado is not None or pais is not None:
            params = (nome, telefone, cpf, estado, pais, roupa, id_cliente)

            query = "UPDATE cliente SET nome = %s, telefone = %s, cpf = %s, estado = %s, pais = %s , roupa = %s WHERE id = %s"
        else:
            params = (nome, telefone, cpf, roupa, id_cliente)

            query = "UPDATE cliente SET nome = %s, telefone = %s, cpf = %s, roupa = %s WHERE id = %s"

        return self.db.execute_query(query, params)

