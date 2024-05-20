import streamlit as st


class RepositoryPagamentos:
    def __init__(self, db):
        self.db = db

    def obter_lancamentos_caixa(self, data, tipo_movimento):
        query = """
        SELECT 
            CASE WHEN tipo IS NULL THEN '' ELSE tipo END,
            CASE WHEN descricao IS NULL THEN '' ELSE descricao END,
            CASE WHEN forma_pg IS NULL THEN '' ELSE forma_pg END,
            CASE WHEN valor IS NULL THEN '' ELSE CONCAT('R$ ', FORMAT(valor, 2, 'de_DE')) END
        FROM caixa WHERE data = %s and tipo_movimento = %s"""
        params = (data, tipo_movimento)

        return self.db.execute_query(query, params)

    def obter_somatorio_caixa(self, data):
        query = f"""
            SELECT 
                
                COALESCE(SUM(CASE WHEN tipo_movimento = 'ENTRADA' AND forma_pg = 'Pix' THEN valor ELSE 0 END), 0) AS soma_pix,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'ENTRADA' AND forma_pg = 'Dinheiro' THEN valor ELSE 0 END), 0) AS soma_dinheiro,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'ENTRADA' AND forma_pg = 'Debito' THEN valor ELSE 0 END), 0) AS soma_debito,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'ENTRADA' AND forma_pg = 'Credito' THEN valor ELSE 0 END), 0) AS soma_credito,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'SAIDA' AND forma_pg = 'Pix' THEN valor ELSE 0 END), 0) AS soma_saida_pix,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'SAIDA' AND forma_pg = 'Dinheiro' THEN valor ELSE 0 END), 0) AS soma_saida_dinheiro,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'SAIDA' AND tipo = 'Cofre' THEN valor ELSE 0 END), 0) AS soma_cofre,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'SAIDA' AND tipo = 'Reembolso' THEN valor ELSE 0 END), 0) AS soma_reembolso,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN valor ELSE 0 END), 0) AS soma_total_entradas,
                COALESCE(SUM(CASE WHEN tipo_movimento = 'SAIDA' THEN valor ELSE 0 END), 0) AS soma_total_saidas,
                COALESCE(
                    (
                        SELECT valor
                        FROM caixa 
                        WHERE tipo_movimento = 'FECHAMENTO' AND data < %s
                        ORDER BY data DESC 
                        LIMIT 1
                    ), 
                    0
                )
            FROM 
                caixa 
            WHERE 
                data = %s"""

        params = (data, data)

        return self.db.execute_query(query, params)

    def select_maquina_cartao(self):
        query = "SELECT nome from maquina_cartao"

        return self.db.execute_query(query)

    def select_info_pagamento_por_maquina_cartao(self, params):
        query = """
        SELECT p.data,
        r.nome_cliente,
        r.tipo,
        p.forma_pg, 
        p.parcela, 
        p.pagamento 
        FROM pagamentos as p 
        INNER JOIN reserva as r on p.id_reserva = r.id where p.maquina = %s"""

        return self.db.execute_query(query, params)

    def obter_valor_pago_por_idreserva(self, id_reserva):
        query = "SELECT recebedor, sum(pagamento) FROM pagamentos WHERE id_reserva = %s GROUP BY recebedor"
        params = (id_reserva,)

        return self.db.execute_query(query, params)

    def insert_pagamentos(self, data, id_reserva, recebedor, pagamento, forma_pg, parcela, id_titular, maquina,
                          tipo_pagamento):
        params = (data, id_reserva, id_titular, recebedor, pagamento, forma_pg, parcela, maquina, tipo_pagamento)

        query = """
        INSERT INTO pagamentos
        (data ,id_reserva, id_titular, recebedor, pagamento, forma_pg, parcela, maquina, tipo_pagamento) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)

    def insert_caixa(self, id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento):
        params = [id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento]

        query = """INSERT INTO caixa (id_conta, data, tipo_movimento, tipo, descricao, forma_pg, valor) VALUES 
            (%s, %s, %s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)

    def insert_maquina_cartao(self, nome, taxa_debito, taxa_credito_vista, taxa_credito_parcelado, taxa_pix):
        params = (nome, taxa_debito, taxa_credito_vista, taxa_credito_parcelado, taxa_pix)

        query = """
        INSERT INTO maquina_cartao (nome, taxa_debito, taxa_credito_vista, taxa_credito_parcelado, taxa_pix)
        VALUES (%s, %s, %s, %s, %s)"""

        return self.db.execute_query(query, params)
