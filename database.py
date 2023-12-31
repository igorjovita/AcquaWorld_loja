import mysql.connector
import os
import dotenv

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USERNAME"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
    ssl_verify_identity=False,
    ssl_ca=r"C:\users\acqua\downloads\cacert-2023-08-22.pem")

cursor = mydb.cursor(buffered= True)
chars = "'),([]"


def lançamento_caixa(data_caixa, id_staff, tipo_lancamento, pagamento_entrada, descricao, valor_entrada):
    cursor.execute(
        "INSERT INTO lancamento_caixa(data, id_staff, tipo_lancamento,  forma_pg  , descricao, valor) VALUES(%s, %s, %s, %s, %s, %s)",
        (data_caixa, id_staff, tipo_lancamento, pagamento_entrada, descricao, valor_entrada))
    mydb.commit()


def cliente(cpf, nome_cliente, telefone_cliente, peso, altura):
    cursor.execute("INSERT INTO cliente (cpf, nome, telefone, peso, altura) VALUES (%s, %s, %s, %s, %s)",
                   (cpf, nome_cliente, telefone_cliente, peso, altura))


def cadastrar_vendedor(nome_vendedor, telefone_vendedor, apelido_vendedor, valor_neto):
    cursor.execute("INSERT INTO vendedores(nome, telefone, apelido, valor neto) VALUES (%s, %s, %s, %s)",
                   (nome_vendedor, telefone_vendedor, apelido_vendedor, valor_neto))


def lista_vendedores():
    cursor.execute("SELECT apelido FROM vendedores")
    dados = cursor.fetchall()
    return dados



def id_vendedor(vendedor):
    cursor.execute(f"SELECT id FROM vendedores WHERE nome = '{vendedor}'")
    id_ven = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
    return id_ven


def id_cliente(nome):
    cursor.execute(f"SELECT id FROM cliente WHERE nome = '{nome}'")
    id_cli = str(cursor.fetchone()).translate(str.maketrans('', '', chars))
    return id_cli
