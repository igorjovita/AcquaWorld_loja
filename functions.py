
def obter_valor_neto(cursor, tipo, valor_total_reserva, id_vendedor_pg):
    if tipo == 'BAT':
        cursor.execute(f"SELECT valor_neto FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'ACP':
        cursor.execute(f"SELECT neto_acp FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'TUR1':
        cursor.execute(f"SELECT neto_tur1 FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'TUR2':
        cursor.execute(f"SELECT neto_tur2 FROM vendedores WHERE id = {id_vendedor_pg}")
    else:
        comissao = valor_total_reserva * 10/100
        valor_neto = valor_total_reserva - comissao
        return valor_neto

    valor_neto = int(cursor.fetchone()[0])
    return valor_neto


def obter_info_reserva(cursor, nome, data_reserva):
    cursor.execute(
        f"SELECT id, id_cliente, tipo, valor_total, receber_loja, id_vendedor FROM reserva WHERE nome_cliente = '{nome}' and data = '{data_reserva}'")
    info_reserva = cursor.fetchone()
    return info_reserva


def update_check_in(cursor, nome, check_in, data_reserva):
    cursor.execute(
        f"UPDATE reserva set check_in = '{check_in}' where nome_cliente = '{nome}' and data = '{data_reserva}'")


def insert_pagamento(cursor, data_pagamento, id_reserva_cliente, recebedor, pagamento, forma_pg, parcela, id_titular_pagamento):
    cursor.execute(
        "INSERT INTO pagamentos (data ,id_reserva, recebedor, pagamento, forma_pg, parcela, id_titular) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (data_pagamento, id_reserva_cliente, recebedor, pagamento, forma_pg, parcela, id_titular_pagamento))
    id_pagamento = cursor.lastrowid
    return id_pagamento


def calcular_valores(valor_neto, acquaworld_valor, vendedor_valor, reserva_neto):

    situacao = 'Pendente'

    if acquaworld_valor < valor_neto:
        valor_receber = valor_neto - acquaworld_valor
        valor_pagar = 0

    elif acquaworld_valor > valor_neto:
        valor_receber = 0
        valor_pagar = acquaworld_valor - valor_neto

    elif acquaworld_valor == valor_neto and vendedor_valor == reserva_neto:
        valor_receber = 0
        valor_pagar = 0
        situacao = 'Pago'

    return valor_receber, valor_pagar, situacao


def insert_lancamento_comissao(cursor, id_reserva_cliente, id_vendedor_pg, valor_receber, valor_pagar, id_titular_pagamento):
    cursor.execute(
        "INSERT INTO lancamento_comissao (id_reserva, id_vendedor, valor_receber, valor_pagar, "
        " id_titular) VALUES (%s, %s, %s, %s, %s)",
        (id_reserva_cliente, id_vendedor_pg,
         valor_receber, valor_pagar, id_titular_pagamento))


def insert_caixa(cursor, id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento):
    cursor.execute(
        "INSERT INTO caixa (id_conta, data, tipo_movimento, tipo, descricao, forma_pg, valor) VALUES "
        "(%s, %s, %s, %s, %s, %s, %s)",
        (id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento))


def processar_pagamento(nome, cursor, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg, id_titular_pagamento):
    # Obter informações da reserva
    info_reserva = obter_info_reserva(cursor, nome, data_reserva)

    # Atualizar o check-in
    update_check_in(cursor, nome, check_in, data_reserva)

    # Extrair informações relevantes
    id_reserva_cliente = info_reserva[0]
    tipo = info_reserva[2]
    valor_total_reserva = info_reserva[3]
    receber_loja_individual = info_reserva[4]

    # Configurar dados de pagamento
    pagamento = receber_loja_individual
    recebedor_pagamento = 'AcquaWorld'

    # Inserir pagamento no banco de dados
    id_pagamento = insert_pagamento(cursor, data_reserva, id_reserva_cliente, recebedor_pagamento, pagamento, forma_pg, parcela, id_titular_pagamento)

    # Calcular soma dos pagamentos
    cursor.execute(
        f"SELECT recebedor, sum(pagamento) FROM pagamentos WHERE id_reserva = {id_reserva_cliente} GROUP BY recebedor")
    resultado_soma = cursor.fetchall()

    # Inicializar variáveis
    vendedor_nome = None
    vendedor_valor = None
    acquaworld_nome = None
    acquaworld_valor = None

    # Calcular valores relevantes
    valor_neto = obter_valor_neto(cursor, tipo, valor_total_reserva, id_vendedor_pg)
    reserva_neto = valor_total_reserva - valor_neto

    for result in resultado_soma:
        nome_result = result[0]
        valor = result[1]

        if nome_result == 'Vendedor':
            vendedor_nome = nome_result
            vendedor_valor = valor
        elif nome_result == 'AcquaWorld':
            acquaworld_nome = nome_result
            acquaworld_valor = valor

    # Calcular valores a receber/pagar
    valor_receber, valor_pagar, situacao = calcular_valores(valor_neto, acquaworld_valor, vendedor_valor, reserva_neto)

    # Criar descrição e inserir no caixa
    data_completa = str(data_reserva).split('-')
    descricao = f'{nome} do dia {data_completa[2]}/{data_completa[1]}/{data_completa[0]}'
    tipo_movimento = 'Entrada'
    id_conta = 1

    insert_caixa(cursor, id_conta, data_reserva, tipo_movimento, tipo, descricao, forma_pg, pagamento)

    # Inserir no lançamento de comissão
    insert_lancamento_comissao(cursor, id_reserva_cliente, id_vendedor_pg, valor_receber, valor_pagar, id_titular_pagamento)

    cursor.execute(f"UPDATE reserva set situacao = 'Reserva Paga' where id = {id_reserva_cliente}")

    return valor_receber, valor_pagar, situacao



