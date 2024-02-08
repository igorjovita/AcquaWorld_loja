import os
import mysql.connector
import streamlit as st
import jinja2
import pdfkit
from babel.numbers import format_currency

chars = "'),([]"
chars2 = "')([]"

# Exemplo de utilização

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem",
    charset="utf8")

cursor = mydb.cursor(buffered=True)


def insert_reserva(reserva):
    mydb.connect()
    sql = (
        "INSERT INTO reserva (data, id_cliente, tipo, id_vendedor, valor_total, nome_cliente, check_in, id_titular, receber_loja) VALUES (%s,%s, %s, %s, %s, %s, %s, %s, %s)")

    # Executar a inserção de múltiplos valores
    cursor.execute(sql, reserva)
    id_reserva = cursor.lastrowid
    mydb.close()
    return id_reserva


def insert_cliente(cpf, nome_cliente, telefone, roupa):
    mydb.connect()
    cursor.execute(
        "INSERT INTO cliente (cpf, nome, telefone, roupa) VALUES (%s, %s, %s, %s)",
        (cpf, nome_cliente, telefone, roupa))
    id_cliente = cursor.lastrowid
    mydb.close()

    return id_cliente


def calculo_restricao(data):
    mydb.connect()
    cursor.execute(f"SELECT COUNT(*) FROM reserva where data = '{data}'")
    contagem = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

    cursor.execute(f"SELECT * FROM restricao WHERE data = '{data}'")
    restricao = cursor.fetchone()

    cursor.execute(
        f"SELECT COUNT(*) FROM reserva WHERE (tipo = 'TUR2' or tipo = 'OWD' or tipo = 'ADV' or tipo = "
        f"'RESCUE' or tipo = 'REVIEW') and data = '{data}'")
    contagem_cred = int(str(cursor.fetchone()).translate(str.maketrans('', '', chars)))

    vaga_bat, vaga_cred, vaga_total = 0, 0, 0  # Inicializa as variáveis

    if restricao is None:
        vaga_cred = 8
        vaga_total = 40
        vaga_bat = vaga_total - contagem_cred
    else:
        cursor.execute(
            f"SELECT vaga_bat, vaga_cred, vaga_total FROM restricao WHERE data = '{data}'")
        restricoes = str(cursor.fetchone()).translate(str.maketrans('', '', chars)).split()
        vaga_bat = int(restricoes[0])
        vaga_cred = int(restricoes[1])
        vaga_total = int(restricoes[2])

    mydb.close()

    return contagem, restricao, contagem_cred, vaga_bat, vaga_cred, vaga_total


@st.cache_resource
def seleciona_vendedores():
    mydb.connect()
    cursor.execute("SELECT apelido FROM vendedores")
    lista_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars)).split()
    mydb.close()
    return lista_vendedor


def seleciona_vendedores_apelido(comissario):
    mydb.connect()
    cursor.execute(f"SELECT id FROM vendedores WHERE apelido = '{comissario}'")
    id_vendedor = str(cursor.fetchall()).translate(str.maketrans('', '', chars))
    mydb.close()

    return id_vendedor

@st.cache_data
def obter_valor_neto(tipo, valor_total_reserva, id_vendedor_pg):
    mydb.connect()

    if tipo == 'BAT':
        cursor.execute(f"SELECT valor_neto FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'ACP':
        cursor.execute(f"SELECT neto_acp FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'TUR1':
        cursor.execute(f"SELECT neto_tur1 FROM vendedores WHERE id = {id_vendedor_pg}")
    elif tipo == 'TUR2':
        cursor.execute(f"SELECT neto_tur2 FROM vendedores WHERE id = {id_vendedor_pg}")
    else:
        # Se o tipo não for 'BAT', 'ACP', 'TUR1' ou 'TUR2', calcula o valor líquido
        comissao = valor_total_reserva * 10 / 100
        valor_neto = valor_total_reserva - comissao
        mydb.close()
        return valor_neto

    # Verifica se a consulta retornou resultados antes de acessar o valor
    resultado = cursor.fetchone()
    mydb.close()

    if resultado is not None:
        valor_neto = int(resultado[0])
        return valor_neto
    else:
        # Trate o caso em que a consulta não retornou resultados
        # Aqui você pode decidir o que fazer se não houver correspondência no banco de dados
        return None

@st.cache_resource
def obter_info_reserva(nome, data_reserva):
    mydb.connect()
    cursor.execute(
        f"SELECT id, id_cliente, tipo, valor_total, receber_loja, id_vendedor FROM reserva WHERE nome_cliente = '{nome}' and data = '{data_reserva}'")
    info_reserva = cursor.fetchone()
    mydb.close()

    return info_reserva


def update_check_in(nome, check_in, data_reserva):
    mydb.connect()
    cursor.execute(
        f"UPDATE reserva set check_in = '{check_in}' where nome_cliente = '{nome}' and data = '{data_reserva}'")
    mydb.close()


def insert_pagamento(data_pagamento, id_reserva_cliente, recebedor, pagamento, forma_pg, parcela, id_titular_pagamento):
    mydb.connect()
    cursor.execute(
        "INSERT INTO pagamentos (data ,id_reserva, recebedor, pagamento, forma_pg, parcela, id_titular) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (data_pagamento, id_reserva_cliente, recebedor, pagamento, forma_pg, parcela, id_titular_pagamento))
    id_pagamento = cursor.lastrowid
    mydb.close()

    return id_pagamento

@st.cache_data
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


def insert_lancamento_comissao(id_reserva_cliente, id_vendedor_pg, valor_receber, valor_pagar, id_titular_pagamento):
    try:
        mydb.connect()
        situacao = 'Pendente'
        cursor.execute(
            "INSERT INTO lancamento_comissao (id_reserva, id_vendedor, valor_receber, valor_pagar, "
            " id_titular, situacao) VALUES (%s, %s, %s, %s, %s, %s)",
            (id_reserva_cliente, id_vendedor_pg,
             valor_receber, valor_pagar, id_titular_pagamento, situacao))
        mydb.commit()  # Certifique-se de commitar a transação
    except Exception as e:
        st.write(f"Erro ao inserir lancamento_comissao: {e}")
    finally:
        mydb.close()


def insert_caixa(id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento):
    try:
        mydb.connect()
        cursor.execute(
            "INSERT INTO caixa (id_conta, data, tipo_movimento, tipo, descricao, forma_pg, valor) VALUES "
            "(%s, %s, %s, %s, %s, %s, %s)",
            (id_conta, data_pagamento, tipo_movimento, tipo, descricao, forma_pg, pagamento))
        mydb.commit()  # Certifique-se de commitar a transação
    except Exception as e:
        st.write(f"Erro ao inserir caixa: {e}")
    finally:
        mydb.close()


def processar_pagamento(nome, data_reserva, check_in, forma_pg, parcela, id_vendedor_pg, id_titular_pagamento):

    # Obter informações da reserva id, id_cliente, tipo, valor_total, receber_loja, id_vendedor
    info_reserva = obter_info_reserva(nome, data_reserva)

    # Atualizar o check-in
    update_check_in(nome, check_in, data_reserva)

    # Extrair informações relevantes
    id_reserva_cliente = info_reserva[0]
    tipo = info_reserva[2]
    valor_total_reserva = info_reserva[3]
    receber_loja_individual = info_reserva[4]

    # Configurar dados de pagamento
    pagamento = receber_loja_individual
    recebedor_pagamento = 'AcquaWorld'

    # Inserir pagamento no banco de dados
    id_pagamento = insert_pagamento(data_reserva, id_reserva_cliente, recebedor_pagamento, pagamento, forma_pg, parcela,
                                    id_titular_pagamento)

    # Calcular soma dos pagamentos
    mydb.connect()
    cursor.execute(
        f"SELECT recebedor, sum(pagamento) FROM pagamentos WHERE id_reserva = {id_reserva_cliente} GROUP BY recebedor")
    resultado_soma = cursor.fetchall()
    mydb.close()
    # Inicializar variáveis
    vendedor_nome = None
    vendedor_valor = None
    acquaworld_nome = None
    acquaworld_valor = None

    # Calcular valores relevantes
    valor_neto = obter_valor_neto(tipo, valor_total_reserva, id_vendedor_pg)
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
    tipo_movimento = 'ENTRADA'
    id_conta = 1

    insert_caixa(id_conta, data_reserva, tipo_movimento, tipo, descricao, forma_pg, pagamento)

    # Inserir no lançamento de comissão
    insert_lancamento_comissao(id_reserva_cliente, id_vendedor_pg, valor_receber, valor_pagar, id_titular_pagamento)

    mydb.connect()
    cursor.execute(f"UPDATE reserva set situacao = 'Reserva Paga' where id = {id_reserva_cliente}")
    mydb.close()

    return valor_receber, valor_pagar, situacao


def select_caixa(data_caixa):
    mydb.connect()
    cursor.execute(
        f"""SELECT id_conta,
                    SUM(CASE WHEN tipo_movimento = 'ENTRADA' 
                        THEN valor 
                        ELSE - valor 
                    END) AS saldo
            FROM caixa where data = '{data_caixa}'""")
    dados = cursor.fetchall()

    mydb.close()
    return dados


def pesquisa_caixa(data_caixa, tipo_movimento):
    mydb.connect()

    cursor.execute(f"""SELECT SUM(CASE WHEN tipo_movimento = 'ENTRADA' THEN valor ELSE - valor END) AS saldo FROM caixa where
    data = '{data_caixa}' and tipo_movimento = '{tipo_movimento}'""")
    dados = cursor.fetchall()
    mydb.close()
    return dados


def info_caixa(tipo_movimento):
    mydb.connect()
    if tipo_movimento == '':
        pass
    else:
        cursor.execute(f"select data,descricao,forma_pg, valor from caixa where tipo_movimento = '{tipo_movimento}'")
        dados = cursor.fetchall()
        return dados
    mydb.close()


def planilha_caixa():
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha_caixa_entrada.html')
    planilha_caixa = planilha.render
    return planilha_caixa


def gerar_pdf(data_para_pdf):
    mydb.connect()
    cliente = []
    cpf = []
    roupa = []
    cert = []
    foto = []
    dm = []
    background_colors = []
    # Consulta ao banco de dados para obter os dados
    cursor.execute(
        f"SELECT nome_cliente, tipo, fotos, dm, check_in FROM reserva WHERE data = '{data_para_pdf}'")
    lista_dados_reserva = cursor.fetchall()

    for dados in lista_dados_reserva:
        if dados[0] is None:
            cliente.append('')
        else:
            cliente.append(
                str(dados[0].encode('utf-8').decode('utf-8')).upper().translate(str.maketrans('', '', chars)))

        if dados[1] is None:
            cert.append('')
        else:
            cert.append(str(dados[1]).upper().translate(str.maketrans('', '', chars)))
        if dados[2] is None:
            foto.append('')
        else:
            foto.append(str(dados[2]).upper().translate(str.maketrans('', '', chars)))

        if dados[3] is None:
            dm.append('')
        else:
            dm.append(str(dados[3]).upper().translate(str.maketrans('', '', chars)))

        background_colors.append(str(dados[4]).translate(str.maketrans('', '', chars)))

    for nome in cliente:
        cursor.execute(
            f"SELECT cpf, roupa FROM cliente WHERE nome = '{nome}'")
        lista_dados_cliente = cursor.fetchall()

        for item in lista_dados_cliente:
            cpf.append(str(item[0]).translate(str.maketrans('', '', chars)))
            roupa.append(str(item[1]).translate(str.maketrans('', '', chars)))

    mydb.close()

    # Processar a data
    data_selecionada = str(data_para_pdf).split('-')
    dia, mes, ano = data_selecionada[2], data_selecionada[1], data_selecionada[0]
    data_completa = f'{dia}/{mes}/{ano}'

    # Criar o contexto
    contexto = {'cliente': cliente, 'cpf': cpf, 'c': cert, 'f': foto,
                'r': roupa, 'data_reserva': data_completa, 'background_colors': background_colors, 'dm': dm}

    # Renderizar o template HTML
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha.html')
    output_text = planilha.render(contexto)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_para_pdf}.pdf"

    # Gerar PDF
    config = pdfkit.configuration()
    options = {
        'encoding': 'utf-8',
        'no-images': None,
        'quiet': '',
    }
    pdfkit.from_string(output_text, pdf_filename, configuration=config, options=options)

    return pdf_filename


def gerar_html(data_para_pdf):
    mydb.connect()
    cliente = []
    cpf = []
    telefone = []
    roupa = []
    id_vendedor = []
    cert = []
    foto = []
    dm = []
    background_colors = []
    lista_id_vendedor = []
    comissario = []
    # Consulta ao banco de dados para obter os dados
    cursor.execute(
        f"SELECT nome_cliente,id_vendedor, tipo, fotos, dm, check_in FROM reserva WHERE data = '{data_para_pdf}'")
    lista_dados_reserva = cursor.fetchall()

    for dados in lista_dados_reserva:
        if dados[0] is None:
            cliente.append('')
        else:
            cliente.append(str(dados[0]).upper().translate(str.maketrans('', '', chars)))

        id_vendedor.append(str(dados[1]).translate(str.maketrans('', '', chars)))

        if dados[2] is None:
            cert.append('')
        else:
            cert.append(str(dados[2]).upper().translate(str.maketrans('', '', chars)))
        if dados[3] is None:
            foto.append('')
        else:
            foto.append(str(dados[3]).upper().translate(str.maketrans('', '', chars)))

        if dados[4] is None:
            dm.append('')
        else:
            dm.append(str(dados[4]).upper().translate(str.maketrans('', '', chars)))

        background_colors.append(str(dados[5]).translate(str.maketrans('', '', chars)))

    for nome in cliente:
        cursor.execute(
            f"SELECT cpf, telefone, roupa FROM cliente WHERE nome = '{nome}'")
        lista_dados_cliente = cursor.fetchall()

        for item in lista_dados_cliente:
            if item[0] is None:
                cpf.append('')
            else:
                cpf.append(str(item[0]).translate(str.maketrans('', '', chars)))

            if item[1] is None:
                telefone.append('')
            else:
                telefone.append(str(item[1]).translate(str.maketrans('', '', chars)))

            if item[2] is None:
                roupa.append('')
            else:
                roupa.append(str(item[2]).translate(str.maketrans('', '', chars)))

    for item in id_vendedor:
        lista_id_vendedor.append(str(item).translate(str.maketrans('', '', chars)))

    for id_v in lista_id_vendedor:
        cursor.execute(f"SELECT apelido from vendedores where id = '{id_v}'")
        comissario.append(str(cursor.fetchone()).upper().translate(str.maketrans('', '', chars)))

    mydb.close()

    # Processar a data
    data_selecionada = str(data_para_pdf).split('-')
    dia, mes, ano = data_selecionada[2], data_selecionada[1], data_selecionada[0]
    data_completa = f'{dia}/{mes}/{ano}'

    # Criar o contexto
    contexto = {'cliente': cliente, 'cpf': cpf, 'tel': telefone, 'comissario': comissario, 'c': cert, 'f': foto,
                'r': roupa, 'data_reserva': data_completa, 'background_colors': background_colors, 'dm': dm}

    # Renderizar o template HTML
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha2.html')
    output_text = planilha.render(contexto)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_para_pdf}.pdf"

    # Gerar PDF
    config = pdfkit.configuration()
    pdfkit.from_string(output_text, pdf_filename, configuration=config)

    return output_text


def gerar_html_entrada_caixa(data_caixa):
    tipo_movimento = []
    tipo = []
    descricao = []
    forma_pg = []
    valor = []
    mydb.connect()
    cursor.execute(f"SELECT tipo_movimento, tipo, descricao, forma_pg, valor FROM caixa WHERE data = '{data_caixa}'")
    dados = cursor.fetchall()

    for dado in dados:
        if dado[0] == 'ENTRADA':

            if dado[0] is None:
                tipo_movimento.append('')
            else:
                tipo_movimento.append(str(dado[0]).translate(str.maketrans('', '', chars)))

            if dado[1] is None:
                tipo.append('')
            else:
                tipo.append(str(dado[1]).translate(str.maketrans('', '', chars)))

            if dado[2] is None:
                descricao.append('')
            else:
                descricao.append(str(dado[2]).translate(str.maketrans('', '', chars)).upper())

            if dado[3] is None:
                forma_pg.append('')
            else:
                forma_pg.append(str(dado[3]).translate(str.maketrans('', '', chars)).upper())

            if dado[4] is None:
                valor.append('')
            else:
                valor_formatado = format_currency(dado[4], 'BRL', locale='pt_BR')
                valor.append(valor_formatado)

    contexto_entrada = {'tipo': tipo, 'descricao': descricao, 'forma_pg': forma_pg, 'valor': valor}

    planilha_loader2 = jinja2.FileSystemLoader('./')
    planilha_env2 = jinja2.Environment(loader=planilha_loader2)
    planilha2 = planilha_env2.get_template('planilha_caixa_entrada.html')
    output_text2 = planilha2.render(contexto_entrada)

    # Nome do arquivo PDF
    pdf_filename2 = f"reservas_{data_caixa}.pdf"

    # Gerar PDF
    config2 = pdfkit.configuration()
    pdfkit.from_string(output_text2, pdf_filename2, configuration=config2)
    mydb.close()

    return output_text2


def gerar_html_saida_caixa(data_caixa):
    tipo_movimento = []
    tipo2 = []
    descricao2 = []
    forma_pg2 = []
    valor2 = []
    mydb.connect()

    cursor.execute(f"SELECT tipo_movimento, tipo, descricao, forma_pg, valor FROM caixa WHERE data = '{data_caixa}'")
    dados = cursor.fetchall()

    for dado in dados:
        if dado[0] == 'SAIDA':

            if dado[1] is None:
                tipo2.append('')
            else:
                tipo2.append(str(dado[1]).translate(str.maketrans('', '', chars)))

            if dado[2] is None:
                descricao2.append('')
            else:
                descricao2.append(str(dado[2]).translate(str.maketrans('', '', chars)).upper())

            if dado[3] is None:
                forma_pg2.append('')
            else:
                forma_pg2.append(str(dado[3]).translate(str.maketrans('', '', chars)).upper())

            if dado[4] is None:
                valor2.append('')
            else:
                valor_formatado = format_currency(dado[4], 'BRL', locale='pt_BR')
                valor2.append(valor_formatado)

    contexto_entrada = {'tipo': tipo2, 'descricao': descricao2, 'forma_pg': forma_pg2, 'valor': valor2}

    planilha_loader2 = jinja2.FileSystemLoader('./')
    planilha_env2 = jinja2.Environment(loader=planilha_loader2)
    planilha2 = planilha_env2.get_template('planilha_caixa_saida.html')
    output_text2 = planilha2.render(contexto_entrada)

    # Nome do arquivo PDF
    pdf_filename2 = f"reservas_{data_caixa}.pdf"

    # Gerar PDF
    config2 = pdfkit.configuration()
    pdfkit.from_string(output_text2, pdf_filename2, configuration=config2)
    mydb.close()

    return output_text2


def gerar_html_total(data_caixa):
    soma_pix = 0
    soma_dinheiro = 0
    soma_credito = 0
    soma_debito = 0
    soma_saida_pix = 0
    soma_saida_dinheiro = 0
    soma_reembolso = 0
    soma_cofre = 0
    mydb.connect()
    cursor.execute(f"SELECT tipo_movimento, tipo, descricao, forma_pg, valor FROM caixa WHERE data = '{data_caixa}'")
    dados = cursor.fetchall()

    for dado in dados:
        if dado[0] == 'ENTRADA':
            if dado[3] == 'Pix':
                soma_pix += float(dado[4])

            if dado[3] == 'Dinheiro':
                soma_dinheiro += float(dado[4])

            if dado[3] == 'Debito':
                soma_debito += float(dado[4])

            if dado[3] == 'Credito':
                soma_credito += float(dado[4])

        if dado[0] == 'SAIDA':
            if dado[3] == 'Pix':
                soma_saida_pix += float(dado[4])

            if dado[3] == 'Dinheiro':
                soma_saida_dinheiro += float(dado[4])

            if dado[1] == 'Cofre':
                soma_cofre += float(dado[4])

            if dado[1] == 'Reembolso':
                soma_reembolso += float(dado[4])

    soma_total_entrada = soma_pix + soma_dinheiro + soma_credito + soma_debito
    soma_total_saida = soma_saida_dinheiro + soma_saida_pix + soma_cofre + soma_reembolso

    soma_pix = format_currency(soma_pix, 'BRL', locale='pt_BR')
    soma_dinheiro = format_currency(soma_dinheiro, 'BRL', locale='pt_BR')
    soma_debito = format_currency(soma_debito, 'BRL', locale='pt_BR')
    soma_credito = format_currency(soma_credito, 'BRL', locale='pt_BR')
    soma_cofre = format_currency(soma_cofre, 'BRL', locale='pt_BR')
    soma_reembolso = format_currency(soma_reembolso, 'BRL', locale='pt_BR')
    soma_saida_pix = format_currency(soma_saida_pix, 'BRL', locale='pt_BR')
    soma_saida_dinheiro = format_currency(soma_saida_dinheiro, 'BRL', locale='pt_BR')

    soma_total_saida = format_currency(soma_total_saida, 'BRL', locale='pt_BR')
    soma_total_entrada = format_currency(soma_total_entrada, 'BRL', locale='pt_BR')

    contexto_total = {'soma_pix': soma_pix, 'soma_dinheiro': soma_dinheiro, 'soma_debito': soma_debito,
                      'soma_credito': soma_credito, 'soma_total_entrada': soma_total_entrada,
                      'soma_reembolso': soma_reembolso, 'soma_saida_pix': soma_saida_pix,
                      'soma_saida_dinheiro': soma_saida_dinheiro, 'soma_cofre': soma_cofre,
                      'soma_total_saida': soma_total_saida}

    # Renderizar o template HTML
    planilha_loader = jinja2.FileSystemLoader('./')
    planilha_env = jinja2.Environment(loader=planilha_loader)
    planilha = planilha_env.get_template('planilha_caixa_total.html')
    output_text = planilha.render(contexto_total)

    # Nome do arquivo PDF
    pdf_filename = f"reservas_{data_caixa}.pdf"

    # Gerar PDF
    config = pdfkit.configuration()
    pdfkit.from_string(output_text, pdf_filename, configuration=config)

    return output_text
