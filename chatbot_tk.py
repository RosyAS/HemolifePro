import tkinter as tk
from tkinter import scrolledtext

respostas = {
    "estoque": "Para consultar o estoque, clique em 'Consultar Estoque' no menu principal.",
    "doar": "Para registrar uma nova doação, vá em 'Registrar Doação'.",
    "relatório": "Você pode gerar relatórios em PDF na seção 'Relatórios'.",
    "alerta": "Alertas de baixo estoque são enviados por email e aparecem nas notificações internas.",
    "requisicao": "Requisições devem ser feitas por médicos e aprovadas pelos técnicos. As aprovadas desaparecem e as rejeitadas ficam no histórico.",
    "código de barras": "Cada bolsa tem um código de barras que pode ser lido com webcam ou scanner. Você pode registrar e escanear pelas opções do menu."
}

def responder(pergunta):
    pergunta = pergunta.lower()
    for chave in respostas:
        if chave in pergunta:
            return respostas[chave]
    return "Desculpe, ainda não sei responder isso. Tente outra pergunta ou fale com o administrador."

def enviar():
    pergunta = entrada.get()
    chatbox.insert(tk.END, "Você: " + pergunta + "\n")
    resposta = responder(pergunta)
    chatbox.insert(tk.END, "Bot: " + resposta + "\n\n")
    entrada.delete(0, tk.END)

def iniciar_chat():
    janela = tk.Tk()
    janela.title("Chatbot - Banco de Sangue")
    janela.geometry("500x400")

    global chatbox, entrada

    chatbox = scrolledtext.ScrolledText(janela, wrap=tk.WORD)
    chatbox.pack(padx=10, pady=10, fill="both", expand=True)

    entrada = tk.Entry(janela)
    entrada.pack(padx=10, pady=5, fill="x")
    entrada.bind("<Return>", lambda e: enviar())

    enviar_btn = tk.Button(janela, text="Enviar", command=enviar)
    enviar_btn.pack(pady=5)

    janela.mainloop()

if __name__ == "__main__":
    iniciar_chat()
