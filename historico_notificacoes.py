import tkinter as tk
from tkinter import ttk
import sqlite3

def carregar_historico(tree):
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome_medico, tipo_sangue, quantidade, status, data
        FROM requisicoes
        WHERE status IN ('aprovada', 'rejeitada')
        ORDER BY data DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)

def historico_interface():
    janela = tk.Tk()
    janela.title("Histórico de Requisições")
    janela.geometry("700x400")

    tree = ttk.Treeview(janela, columns=("ID", "Médico", "Tipo", "Qtd", "Status", "Data"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER)
    tree.pack(expand=True, fill="both")

    carregar_historico(tree)
    janela.mainloop()

if __name__ == "__main__":
    historico_interface()
