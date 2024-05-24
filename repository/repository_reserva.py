import streamlit as st


class RepositoryReserva:
    def __init__(self, db):
        self.db = db

    def obter_nome_id_tipo_reserva_por_data(self, data):
        params = (data,)
        query = ("""
        SELECT 
            reserva.data,
            cliente.id,
            cliente.nome,
            cliente.cpf,
            cliente.telefone,
            cliente.roupa,
            reserva.tipo,
            reserva.id_titular,
            vendedores.nome,
            vendedores.id,
            reserva.valor_total,
            reserva.receber_loja,
            reserva.data_pratica2 
        from reserva 
        inner join cliente on reserva.id_cliente = cliente.id 
        inner join vendedores on reserva.id_vendedor = vendedores.id
        where reserva.data = %s""")
        return self.db.execute_query(query, params)

    def obter_info_reserva_por_cliente_data(self, nome_cliente, data):
        params = (nome_cliente, data)
        query = f"SELECT id, id_cliente, tipo, valor_total, receber_loja, id_vendedor FROM reserva WHERE nome_cliente = %s and data = %s"
        return self.db.execute_query(query, params)

    def obter_info_reserva_pagamentos_por_id(self, id_titular):
        params = (id_titular,)
        query = """WITH SomaPagamento as (
                    SELECT 
                        p.id_reserva,
                        SUM(p.pagamento) as total_pago
                    from pagamentos p 
                    LEFT JOIN reserva as r ON p.id_reserva = r.id
                    GROUP BY p.id_reserva
                    )
                SELECT 
                    r.nome_cliente,
                    r.id_cliente,
                    r.id,
                    CASE  WHEN sp.total_pago >= r.valor_total OR r.receber_loja = sp.total_pago OR r.receber_loja IS NULL THEN 0.00 ELSE r.receber_loja END as receber_loja,
                    r.id_vendedor,
                    r.tipo,
                    r.valor_total,
                    CASE WHEN r.situacao IS NULL THEN 'Pendente' else r.situacao end as situacao,
                    p.recebedor,
                    r.id_titular,
                    sp.total_pago as total_pago,
                    CASE WHEN r.desconto IS NULL THEN 0 ELSE r.desconto END AS desconto
                from reserva as r 
                LEFT JOIN pagamentos as p ON p.id_reserva = r.id 
                LEFT JOIN SomaPagamento as sp ON r.id = sp.id_reserva
                where r.id_titular = %s
                GROUP BY r.id, p.recebedor"""

        return self.db.execute_query(query, params)

    def obter_info_reserva_para_planilha_loja(self, data):

        query = """
        SELECT 
            r.nome_cliente AS nome_cliente, 
            CASE WHEN cpf = CONCAT(c.nome, ' ', data) THEN ' '  ELSE cpf END,
            c.telefone, 
            v.apelido,
            r.tipo,
            r.fotos,
            c.roupa,
            r.check_in,
            r.observacao
        FROM reserva AS r 
        INNER JOIN cliente AS c ON r.id_cliente = c.id 
        INNER JOIN vendedores AS v ON r.id_vendedor = v.id 
        WHERE r.data = %s"""

        params = (data,)

        return self.db.execute_query(query, params)

    def obter_info_pagamento_para_tabela_pagamentos(self, id_titular):

        params = (id_titular,)
        query = """
        WITH SomaPagamento as (
                    SELECT 
                        p.id_reserva,
                        SUM(p.pagamento) as total_pago
                    from pagamentos p 
                    LEFT JOIN reserva as r ON p.id_reserva = r.id
                    GROUP BY p.id_reserva
                    )
                SELECT
                    r.nome_cliente,
                    r.tipo,
                    v.nome AS nome_vendedor,
                    r.valor_total,
                    r.receber_loja,
                    CONCAT(p1.pagamento, ' - ', p1.recebedor),
                    CONCAT(p2.pagamento, ' - ', p2.recebedor),
                    CASE 
                        WHEN sp.total_pago >= r.valor_total OR r.receber_loja = sp.total_pago THEN 'Reserva Paga' 
                        WHEN r.situacao IS NULL THEN 'Pendente' 
                        ELSE r.situacao 
                    END AS situacao

                FROM reserva AS r 
                LEFT JOIN pagamentos AS p1 ON p1.id_reserva = r.id AND p1.tipo_pagamento = 'Sinal'
                LEFT JOIN pagamentos AS p2 ON p2.id_reserva = r.id AND p2.tipo_pagamento = 'Pagamento'
                LEFT JOIN vendedores AS v ON v.id = r.id_vendedor 
                LEFT JOIN SomaPagamento as sp ON r.id = sp.id_reserva
                WHERE r.id_titular = %s;"""

        return self.db.execute_query(query, params)

    def obter_info_titular_reserva_por_data(self, data):
        params = (data,)
        query = "SELECT nome_cliente, id_cliente FROM reserva WHERE data = %s and id_titular = id_cliente"
        return self.db.execute_query(query, params)

    def obter_info_grupo_reserva_por_titular_data(self, params):
        query = "SELECT id_cliente, nome_cliente, tipo FROM reserva WHERE id_titular = %s and data = %s"
        return self.db.execute_query(query, params)

    def obter_ids_reserva_por_id_cliente(self, id_cliente):
        query = "SELECT id, id_titular, id_vendedor FROM reserva where id_cliente = %s"

        params = (id_cliente,)

        return self.db.execute_query(query, params)

    def obter_contagem_reserva(self, data):
        query = """
        SELECT
            IFNULL(SUM(CASE WHEN tipo = 'BAT' THEN 1 ELSE 0 END), 0) AS BAT,
            IFNULL(SUM(CASE WHEN tipo = 'ACP' THEN 1 ELSE 0 END), 0) AS ACP,
            IFNULL(SUM(CASE WHEN tipo = 'TUR1' THEN 1 ELSE 0 END), 0) AS TUR1,
            IFNULL(SUM(CASE WHEN tipo = 'TUR2' THEN 1 ELSE 0 END), 0) AS TUR2,
            IFNULL(SUM(CASE WHEN tipo = 'OWD' THEN 1 ELSE 0 END), 0) AS OWD,
            IFNULL(SUM(CASE WHEN tipo = 'ADV' THEN 1 ELSE 0 END), 0) AS ADV,
            IFNULL(SUM(CASE WHEN tipo = 'RESCUE' THEN 1 ELSE 0 END), 0) AS RESCUE,
            IFNULL(SUM(CASE WHEN tipo = 'DIVEMASTER' THEN 1 ELSE 0 END), 0) AS DIVEMASTER,
            IFNULL(SUM(CASE WHEN tipo IN ('OWD', 'ADV', 'TUR2', 'TUR1', 'RESCUE', 'DIVEMASTER') THEN 1 ELSE 0 END), 0) AS TOTAL_CURSO_CRED,
            COUNT(*) AS TOTAL
        FROM reserva
        WHERE data = %s;"""
        params = (data,)

        return self.db.execute_query(query, params)

    def obter_contagem_restricao(self, data):

        query = "SELECT vaga_bat, vaga_cred, vaga_total FROM restricao WHERE data = %s"
        params = (data,)

        return self.db.execute_query(query, params)

    def insert_reserva(self, data, id_cliente, tipo, id_vendedor, valor_total, nome_cliente, id_titular,
                       receber_loja, observacao, desconto):

        params = (data, id_cliente, tipo, id_vendedor, valor_total, nome_cliente,  id_titular, receber_loja, observacao, desconto)
        query = """
        INSERT INTO reserva 
        (data, id_cliente, tipo, id_vendedor, valor_total, nome_cliente, id_titular, receber_loja, observacao, desconto) 
        VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)

    def update_reserva_info_termo(self, nome_cliente, id_cliente):
        params = (nome_cliente, id_cliente)

        query = ("UPDATE reserva set nome_cliente = CASE WHEN tipo != 'OWD' AND tipo != 'ADV' THEN %s END WHERE "
                 "id_cliente = %s and data = %s")

        return self.db.execute_query(query, params)

    def update_reserva_tela_editar(self, novo_data_reserva, novo_tipo, id_novo_vendedor, novo_valor_total,
                                   novo_valor_receber, novo_data_pratica2, id_cliente):
        params = (
        novo_data_reserva, novo_tipo, id_novo_vendedor, novo_valor_total, novo_valor_receber, novo_data_pratica2,
        id_cliente)

        query = """
        UPDATE reserva SET 
            data = %s,  
            tipo = %s, 
            id_vendedor = %s,
            valor_total = %s,  
            receber_loja = %s, 
            data_pratica2 = %s 
        WHERE id_cliente = %s"""

        return self.db.execute_query(query, params)

    def update_reserva_grupo_tela_editar(self, novo_data_reserva, id_novo_vendedor, id_tiular):

        query = "UPDATE reserva set data_reserva = %s, id_vendedor = %s WHERE id_titular = %s"

        params = (novo_data_reserva, id_novo_vendedor, id_tiular)

        return self.db.execute_query(query, params)

    def update_reserva_parcial(self, id_cliente, nome_cliente, tipo, valor_total, receber_loja):
        params = (nome_cliente, tipo, valor_total, receber_loja, id_cliente)

        query = ("UPDATE reserva set nome_cliente = %s, tipo = %s, valor_total = %s, receber_loja = %s WHERE "
                 "id_cliente = %s")

        return self.db.execute_query(query, params)

    def update_cor_fundo_reserva(self, status, nome_cliente, data):

        if status == 'Chegou na Loja':
            codigo_cor = '#00B0F0'
        elif status == 'Direto pro Pier':
            codigo_cor = 'yellow'
        else:
            codigo_cor = 'FFFFFF'

        query = "UPDATE reserva set check_in = %s where nome_cliente = %s and data = %s"
        params = (codigo_cor, nome_cliente, data)
        return self.db.execute_query(query, params)

    def update_situacao_reserva(self, id_reserva):

        query = "UPDATE reserva set situacao = 'Reserva Paga' where id = %s"
        params = (id_reserva,)

        return self.db.execute_query(query, params)

    def tabela_comissao(self):

        query = """
        SELECT 
            reserva.Data as Data,
            reserva.nome_cliente as Nome_Titular,
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
            reserva.Data BETWEEN %s and %s AND
            lancamento_comissao.Id_vendedor = %s AND
            lancamento_comissao.situacao = %s
        GROUP BY reserva.Id_titular, reserva.Data, lancamento_comissao.situacao
        """
