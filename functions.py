import streamlit as st

def obter_valor_neto(cursor, tipo, id_vendedor_pg):
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