import mysql.connector
import streamlit as st


class RepositoryVendedor:
    def __init__(self, db):
        self.db = db

    def select_id_apelido(self):
        query = "SELECT id, apelido FROM vendedores"

        return self.db.execute_query(query)

    def select_nome_neto(self):
        query = "SELECT apelido, valor_neto, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2 FROM vendedores order by valor_neto asc "
        return self.db.execute_query(query)

    def select_vendedor_id(self, apelido):
        query = "SELECT id FROM vendedores WHERE apelido = %s"
        params = (apelido, )
        return self.db.execute_query(query, params)

    def select_valor_neto(self, id_vendedor):

        query = "SELECT valor_neto, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2 FROM vendedores WHERE id = %s"

        params = (id_vendedor, )

        return self.db.execute_query(query, params)

    def select_tabela_comissao(self, id_vendedor, data1=None, data2=None, situacao=None):
        params = [id_vendedor]

        query = """
            SELECT 
                cliente.id as id_cliente,
                reserva.Data as Data,
                cliente.nome as Nome_Titular,
                (SELECT GROUP_CONCAT(CONCAT(contagem, ' ', tipo) SEPARATOR ' + ')
                 FROM (
                   SELECT tipo, COUNT(*) AS contagem
                   FROM reserva AS r2
                   WHERE r2.Id_titular = reserva.Id_titular AND r2.Data = reserva.Data
                   GROUP BY tipo
                 ) AS subconsulta) as Tipos_Reserva,
                SUM(lancamento_comissao.valor_receber) as Valor_Receber,
                SUM(lancamento_comissao.valor_pagar) as Valor_Pagar,
                COALESCE(SUM(pagamentos_soma.pagamento), 0) as Valor_Pago,
                lancamento_comissao.situacao
            FROM 
                reserva
            JOIN 
                lancamento_comissao ON reserva.Id = lancamento_comissao.Id_reserva
            JOIN 
                vendedores ON lancamento_comissao.Id_vendedor = vendedores.Id
            JOIN cliente ON cliente.id = reserva.id_cliente
            LEFT JOIN (
                SELECT Id_titular, Data, COUNT(*) as cnt
                FROM reserva
                GROUP BY Id_titular, Data
            ) as cnt_reserva ON reserva.Id_titular = cnt_reserva.Id_titular AND reserva.Data = cnt_reserva.Data
            LEFT JOIN (
                SELECT id_reserva, SUM(pagamento) as pagamento
                FROM pagamentos
                WHERE recebedor = 'AcquaWorld'
                GROUP BY id_reserva
            ) as pagamentos_soma ON reserva.Id = pagamentos_soma.id_reserva
            WHERE  
                lancamento_comissao.Id_vendedor = %s
        """

        if data1 is not None:
            query += " AND reserva.Data BETWEEN %s and %s"
            params.append(data1)
            params.append(data2)

        if situacao is not None:
            query += " AND lancamento_comissao.situacao = %s"
            params.append(situacao)
        query += "\n GROUP BY reserva.Id_titular, reserva.Data, lancamento_comissao.situacao"

        params = tuple(params)

        return self.db.execute_query(query, params)

    def select_id_lancamento_comissao(self, id_titular):

        query = """
        SELECT id FROM lancamento_comissao WHERE id_titular = %s
        """
        params = (id_titular, )

        return self.db.execute_query(query, params)


    def update_lancamento_comissao(self, situacao, id_comissao):
        query = """UPDATE lancamento_comissao SET situacao = %s where id = %s """

        params = (situacao, id_comissao)

        return self.db.execute_query(query, params)

    def insert_vendedores(self, nome, apelido, telefone, neto_bat, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2):

        params = (nome, apelido, telefone, neto_bat, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2)

        query = """
        INSERT INTO vendedores 
        (nome, apelido, telefone, valor_neto, neto_bat_cartao, neto_acp, neto_tur1, neto_tur2) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)

    def insert_lancamento_comissao(self, id_reserva, id_vendedor, valor_receber, valor_pagar, id_titular, situacao):
        params = (id_reserva, id_vendedor, valor_receber, valor_pagar, id_titular, situacao)

        query = """INSERT INTO lancamento_comissao 
        (id_reserva, id_vendedor, valor_receber, valor_pagar, id_titular, situacao) VALUES (%s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)






