from .repository_cliente import RepositoryCliente
from .repository_reserva import RepositoryReserva
class RepositoryTermo:

    def __init__(self, db):
        self.db = db

    def obter_info_relacao_termo_idcliente_por_data(self, data):
        params = (data,)

        query = """
            SELECT
            id_cliente,
            nome,
            CASE WHEN id_cliente IS NOT NULL THEN 'relacionado ao cliente' ELSE 'nao relacionado' END 
            FROM termo_clientes
            WHERE data_reserva = %s"""

        return self.db.execute_query(query, params)

    def obter_info_gerar_termo_por_data_nome(self, data, nome):
        params = (data, nome)

        query = """
        SElECT c.nome, c.telefone, c.cpf, c.data_nascimento, c.email,
        c.nome_emergencia, c.telefone_emergencia, c.estado, c.pais, c.data_reserva,
        m.gravida, m.remedio, m.doenca_cardiaca, m.asma, m.doenca_pulmonar, m.epilepsia,
        m.enjoo, m.dd, m.coluna, m.diabetes, m.ouvido, m.hemorragia, m.sinusite, m.cirurgia,
        m.nome_cirurgia, m.tempo_cirurgia, m.viagem, m.menor, m.bebida
        from termo_clientes as c 
        INNER JOIN termo_medico as m on m.id_termo_cliente = c.id 
        where c.data_reserva = %s and c.nome = %s"
        """
        return self.db.execute_query(query, params)

    def select_info_termo_data(self, data):
        params = (data, )

        query = """
        SELECT id_cliente, nome from termo_clientes where data_reserva = %s
        """

        return self.db.execute_query(query, params)

    def update_termo_cliente(self, id_cliente, nome):
        query = "UPDATE termo_clientes set id_cliente = %s where nome = %s"
        params = (id_cliente, nome)

        self.db.execute_query(query, params)



