import sqlite3
import barcode
from barcode.writer import ImageWriter

def gerar_codigo_barras_para_doacao(id_doacao, tipo_sangue):
    codigo = f"{tipo_sangue}-{id_doacao}"
    codigo_barras = barcode.get('code128', codigo, writer=ImageWriter())
    filename = f"codigos/{codigo}"
    codigo_barras.save(filename)
    print(f"✅ Código gerado: {filename}.png")

# Exemplo: após cadastrar doação
if __name__ == "__main__":
    gerar_codigo_barras_para_doacao(12, "O+")
