import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# Atualiza visualização
def carregar_requisicoes(tree):
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_medico, tipo_sangue, quantidade, status FROM requisicoes WHERE status = 'pendente'")
    rows = cursor.fetchall()
    conn.close()

    tree.delete(*tree.get_children())  # limpa tabela
    for row in rows:
        tree.insert("", "end", values=row)

# Aprovar
def aprovar(tree):
    item = tree.selection()
    if item:
        requisicao_id = tree.item(item)["values"][0]
        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE requisicoes SET status='aprovada' WHERE id=?", (requisicao_id,))
        conn.commit()
        conn.close()
        carregar_requisicoes(tree)
        messagebox.showinfo("Sucesso", "Requisição aprovada!")

# Rejeitar
def rejeitar(tree):
    item = tree.selection()
    if item:
        requisicao_id = tree.item(item)["values"][0]
        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE requisicoes SET status='rejeitada' WHERE id=?", (requisicao_id,))
        conn.commit()
        conn.close()
        carregar_requisicoes(tree)
        messagebox.showinfo("Info", "Requisição rejeitada!")

# Interface principal
def requisicoes_interface():
    janela = tk.Tk()
    janela.title("Aprovar/Rejeitar Requisições")
    janela.geometry("600x400")
    janela.configure(bg="#f5f5f5")

    label = tk.Label(janela, text="Requisições Pendentes", font=("Helvetica", 16, "bold"), bg="#f5f5f5")
    label.pack(pady=10)

    tree = ttk.Treeview(janela, columns=("ID", "Médico", "Tipo", "Quantidade", "Status"), show="headings")
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER)
    tree.pack(pady=20, fill=tk.BOTH, expand=True)

    frame_botoes = tk.Frame(janela, bg="#f5f5f5")
    frame_botoes.pack()

    btn_aprovar = tk.Button(frame_botoes, text="Aprovar", width=15, bg="green", fg="white",
                            command=lambda: aprovar(tree))
    btn_aprovar.pack(side=tk.LEFT, padx=10)

    btn_rejeitar = tk.Button(frame_botoes, text="Rejeitar", width=15, bg="red", fg="white",
                             command=lambda: rejeitar(tree))
    btn_rejeitar.pack(side=tk.LEFT, padx=10)

    carregar_requisicoes(tree)
    janela.mainloop()

if __name__ == "__main__":
    requisicoes_interface()
