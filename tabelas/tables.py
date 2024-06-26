import streamlit as st
import streamlit.components.v1
from datetime import datetime
import pdfkit


class Planilhas:
    def __init__(self, repository_reserva):
        self.repository_reserva = repository_reserva

    def planilha_loja(self, data):

        dados_planilha_loja = self.repository_reserva.obter_info_reserva_para_planilha_loja(data)

        html_table = """
        <table style="border-collapse: collapse; width: 100%;" border="1">
            <tbody>
                <tr style="height: 30px;">
                    <th style="text-align: center;">#</th>
                    <th>Nome Cliente</th>
                    <th>Telefone</th>
                    <th>Observação</th>
                    <th>Vendedor</th>
                    <th>Tipo</th>
                    <th>Fotos</th>
                    <th>Roupa</th>
                </tr>
        """

        minimo = 10
        for i, dado in enumerate(dados_planilha_loja):
            name = str(dado[0]).upper() if dado[0] is not None else ''
            # cpf = dado[1] if dado[1] is not None else ''
            telefone = dado[2] if dado[2] is not None else ''
            comissario = str(dado[3]).upper() if dado[3] is not None else ''
            tipo = dado[4] if dado[4] is not None else ''
            fotos = dado[5] if dado[5] is not None else ''
            roupa = dado[6] if dado[6] is not None else ''
            cor_fundo = dado[7] if dado[7] is not None else ''
            observacao = dado[8] if dado[8] is not None else ''

            html_table += f"""
                    <tr style="height: 30px;">
                        <td style="text-align: center;">{i + 1}</td>
                        <td style= "background-color: {cor_fundo};">{name}</td> 
                        <td>{telefone}</td> 
                        <td>{observacao}</td>
                        <td>{comissario}</td>
                        <td>{tipo}</td>
                        <td>{fotos}</td>
                        <td>{roupa}</td>
                    </tr>
                """
        if len(dados_planilha_loja) < minimo:
            numero = minimo - len(dados_planilha_loja)

            for i in range(numero):
                html_table += f"""
                    <tr style="height: 30px;">
                        <td style="text-align: center;">{len(dados_planilha_loja) + i + 1}</td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                        <td></td>
                    </tr>
                    """

        html_table += "</tbody></table>"
        html_table = st.components.v1.html(html_table, height=1000, width=1000, scrolling=True)

        return html_table

    def planilha_barco(self, data, barco):

        dados_para_planilha = self.repository_reserva.obter_info_reserva_para_planilha_loja(data)

        html_table = f"""
                    <h3 style="text-align: center; margin-top: 40px;"><strong>Planilha Operação Diaria</strong></h3>
                    <h4 style= "margin: 0;">Embarcação {barco}</h4>
                    <div style="display: flex;">
                        <h4>Data: {datetime.strptime(str(data), '%Y-%m-%d').strftime('%d/%m/%Y')}</h4>
                        <h4 style="margin-left: 50px;">Horario: 09:00</h4>
                    </div>
                    <table style="border-collapse: collapse; width: 100%;" border="1">
                    <tbody>
                        <tr style="height: 30px;">
                            <th style="text-align: center; border: 1px solid black; font-size: 13px;">#</th>
                            <th style="border: 1px solid black; font-size: 13px;">NOME COMPLETO</th>
                            <th style="width: 150px; border: 1px solid black; font-size: 13px;">CPF</th>
                            <th style="border: 1px solid black; font-size: 13px;">OBSERVAÇÃO</th>
                            <th style="border: 1px solid black; font-size: 13px;">CERT</th>
                            <th style="width: 15px; border: 1px solid black; font-size: 13px;">FOTOS</th>
                            <th style="width: 20px; border: 1px solid black; font-size: 13px;">ROUPA</th>
                            <th style="border: 1px solid black; font-size: 13px;">BATERIA</th>
                        </tr>

                """

        for i, dado in enumerate(dados_para_planilha):
            nome_cliente = str(dado[0]).upper() if dado[0] is not None else ''
            cpf = dado[1] if dado[1] is not None else ''
            tipo = dado[4] if dado[4] is not None else ''
            fotos = dado[5] if dado[5] is not None else ''
            roupa = dado[6] if dado[6] is not None else ''
            cor_fundo = dado[7] if dado[7] is not None else ''
            observacao = dado[8] if dado[8] is not None else ''

            html_table += f"""
                        <tr style="height: 30px;">
                            <td style="text-align: center; border: 1px solid black; font-size: 13px;">{i + 1}</td>
                            <td style="background-color: {cor_fundo}; border: 1px solid black; font-size: 13px;">{nome_cliente}</td>
                            <td style="border: 1px solid black; font-size: 13px;">{cpf}</td>
                            <td style="border: 1px solid black; font-size: 13px;">{observacao}</td>
                            <td style="border: 1px solid black; font-size: 13px;">{tipo}</td>
                            <td style="border: 1px solid black; font-size: 13px;">{fotos}</td>
                            <td style="width: 20px; border: 1px solid black; font-size: 13px;">{roupa}</td>
                            <td style="border: 1px solid black; font-size: 13px;"></td>
                        </tr>

                    """
        minimo = 25
        if len(dados_para_planilha) < minimo:
            numero = minimo - len(dados_para_planilha)

            for i in range(numero):
                html_table += f"""
                                <tr style="height: 30px;">
                                    <td style="text-align: center; border: 1px solid black; font-size: 13px;">{len(dados_para_planilha) + i + 1}</td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                    <td style="border: 1px solid black; font-size: 13px;"></td>
                                </tr>

                            """

        html_table += """
                    <td style="border-style: solid; height: 18px; background-color: #808080; border-color: #000000; text-align: center; border: 2px solid black; font-size: 12px;" colspan="8">STAFFS</td>
                    <tr style="height: 20px;">
                        <th style="text-align: center; border: 2px solid black; font-size: 12px;">#</th>
                        <th style="border: 1px solid black; font-size: 13px;">NOME</th>
                        <th style="border: 1px solid black; font-size: 13px;">CPF</th>
                        <th style="border: 1px solid black; font-size: 13px;">BAT</th>
                        <th style="width: 15px; border: 1px solid black; font-size: 13px;">TUR</th>
                        <th style="border: 1px solid black; font-size: 13px;">CURSO</th>
                        <th style="width: 20px; border: 1px solid black; font-size: 13px;">ASSINATURA</th>
                        <th style="border: 1px solid black; font-size: 13px;">OBSERVAÇÃO</th>
                    </tr>
                    """
        for i in range(10):
            html_table += f"""
                    <tr style="height: 30px;">
                        <td style="text-align: center; border: 1px solid black; font-size: 13px;">{i + 1}</td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                        <td style="border: 1px solid black; font-size: 13px;"></td>
                    </tr>
                """

        html_table += "</tbody></table>"

        # Nome do arquivo PDF
        pdf_filename = f"reservas_{data}.pdf"

        # Gerar PDF
        config = pdfkit.configuration()
        options = {
            'encoding': 'utf-8',
            'no-images': None,
            'quiet': '',
        }
        pdfkit.from_string(html_table, pdf_filename, configuration=config, options=options)

        return pdf_filename
