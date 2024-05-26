from openpyxl import load_workbook
import calendar


class Excel:
    def __init__(self, caminho_arquivo, wb_modelo):

        self.caminho = caminho_arquivo
        self.wb = load_workbook(caminho_arquivo)
        self.ws = None
        self.wb_modelo = wb_modelo

    def selecionar_sheet_por_data(self, data):
        """
        Seleciona a sheet com base na data fornecida.

        :param data: Data no formato 'dd-mm-yyyy'.
        """
        data = str(data).split('-')
        nome_sheet = f'{data[2]}.{data[1][1]}'
        if nome_sheet in self.wb.sheetnames:
            self.ws = self.wb[nome_sheet]
        else:
            print(f"Sheet '{nome_sheet}' não encontrada.")
            self.ws = None

    def insert_excel(self, dados_cliente, data):

        self.selecionar_sheet_por_data(data)

        if self.ws is None:
            print('Erro - Sheet nao selecionada')
            return

        coluna_nome_cliente = 2
        coluna_telefone = 3
        coluna_comissario = 4
        coluna_cert = 5
        coluna_roupa = 8

        for row in self.ws.iter_rows(min_row=6, max_row=19, min_col=2, max_col=2):
            for cell in row:
                print(cell.value)

        proxima_linha_vazia = None
        for row in range(6, self.ws.max_row + 2):
            linha_vazia = True
            for col in range(2, 8):  # Colunas B (2) a G (7)
                cell = self.ws.cell(row=row, column=col)
                if cell.value is not None:
                    linha_vazia = False
                    break
            if linha_vazia:
                proxima_linha_vazia = row
                break

        if proxima_linha_vazia is not None:
            for cliente in dados_cliente:
                self.ws.cell(row=proxima_linha_vazia, column=coluna_nome_cliente, value=cliente[0])
                self.ws.cell(row=proxima_linha_vazia, column=coluna_telefone, value=cliente[1])
                self.ws.cell(row=proxima_linha_vazia, column=coluna_comissario, value=cliente[2])
                self.ws.cell(row=proxima_linha_vazia, column=coluna_cert, value=cliente[3])
                self.ws.cell(row=proxima_linha_vazia, column=coluna_roupa, value=cliente[4])
                proxima_linha_vazia += 1
        else:
            print('Não foi encontrado linha vazia na coluna B')

        self.wb.save(r"C:\Users\Igorj\Downloads\MAIO 2024-teste.xlsx")

    def encontrar_linha_pelo_nome(self, nome_cliente, coluna):
        if self.ws is None:
            print("Erro: Sheet não selecionada.")
            return None

        for row in range(6, self.ws.max_row + 1):  # Começa a partir da linha 6
            cell = self.ws.cell(row=row, column=coluna)
            if cell.value == nome_cliente:
                return row

        print(f"Nome '{nome_cliente}' não encontrado na coluna B.")
        return None

    def alterar_informacao(self, nome, data, coluna, novo_valor):

        num_colunas = {
            'coluna_nome_cliente': 2,
            'coluna_telefone': 3,
            'coluna_comissario': 4,
            'coluna_cert': 5,
            'coluna_roupa': 8
        }

        coluna = num_colunas[f'coluna_{coluna}']

        self.selecionar_sheet_por_data(data)

        if self.ws is None:
            print('Erro - Sheet nao selecionada')
            return

        row = self.encontrar_linha_pelo_nome(nome, 2)

        self.ws.cell(row=row, column=coluna, value=novo_valor)
        self.wb.save(self.caminho)

        print('Dados Alterados com Sucesso')

    def deletar_linha(self, nome, data):

        self.selecionar_sheet_por_data(data)
        row = self.encontrar_linha_pelo_nome(nome, 2)
        row_final = self.encontrar_linha_pelo_nome('STAFFS', 3)

        self.ws.delete_rows(row)
        row_final = row_final - 1
        self.ajustar_contagem(row_final)
        self.wb.save(self.caminho)
        print('Linha Excluida com Sucesso!')

    def ajustar_contagem(self, ultima_linha):

        contagem = 1
        for row in range(6, ultima_linha):
            self.ws.cell(row=row, column=1, value=contagem)  # Atualizar a contagem na coluna A
            contagem += 1

    def criar_planilha(self, ano, mes):

        sheet_modelo = self.wb_modelo['Modelo']
        num_dias = calendar.monthrange(ano, mes)[1]

        for dia in range(1, num_dias + 1):
            nome_sheet = f'{dia}.{mes}'

            # Copiar a sheet modelo
            nova_sheet = self.wb_modelo.copy_worksheet(sheet_modelo)
            nova_sheet.title = nome_sheet

        self.wb_modelo.save(r"C:\Users\Igorj\Downloads\MAIO 2024-teste.xlsx")

        print(num_dias)
