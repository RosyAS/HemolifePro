import tkinter as tk
from tkinter import messagebox
import subprocess
import sys

# Função para chamar outro script
def abrir_script(nome_arquivo):
    try:
        subprocess.Popen([sys.executable, nome_arquivo])
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir {nome_arquivo}.\n{e}")

# Tela principal
class MenuPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Banco de Sangue")
        self.root.geometry("400x500")
        self.root.configure(bg="#8B0000")  # vermelho escuro

        titulo = tk.Label(root, text="Painel Principal", font=("Helvetica", 18, "bold"), fg="white", bg="#8B0000")
        titulo.pack(pady=20)

        botoes = [
            ("Cadastrar Doações", "cadastro_kivy.py"),
            ("Gerenciar Requisições", "requisicoes.py"),
            ("Gerar Relatório", "relatorio.py"),
            ("Previsão de Demanda", "previsao.py"),
            ("Chatbot", "chatbot.py"),
            ("Sair do Sistema", None),
        ]

        for texto, script in botoes:
            btn = tk.Button(root, text=texto, width=30, height=2,
                            command=(lambda s=script: self.abrir_ou_sair(s)),
                            bg="white", fg="black", font=("Helvetica", 10, "bold"))
            btn.pack(pady=10)

    def abrir_ou_sair(self, script):
        if script:
            abrir_script(script)
        else:
            self.root.destroy()

# Executar interface
if __name__ == "__main__":
    root = tk.Tk()
    app = MenuPrincipal(root)
    root.mainloop()
