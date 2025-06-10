import sqlite3
from fpdf import FPDF
from tkinter import messagebox
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# CONFIGURAÇÃO DO ALERTA POR EMAIL
EMAIL_ORIGEM = "teusistema@gmail.com"
EMAIL_DESTINO = "chefe.seccao@exemplo.com"
EMAIL_SENHA = "sua_senha_aqui"  # use um app password para Gmail

# SIMULAÇÃO DE SMS
def simular_sms(tipo, quantidade):
    print(f"📱 ALERTA SMS: Sangue tipo {tipo} está com nível crítico ({quantidade} unidades).")

# ENVIA EMAIL
def enviar_email(tipo, quantidade):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ORIGEM
    msg['To'] = EMAIL_DESTINO
    msg['Subject'] = f"⚠️ Alerta de Estoque - Sangue {tipo}"

    corpo = f"""
    Atenção,

    O estoque do sangue tipo {tipo} está crítico com apenas {quantidade} unidades disponíveis.

    Sistema Banco de Sangue - {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}
    """

    msg.attach(MIMEText(corpo, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ORIGEM, EMAIL_SENHA)
        server.send_message(msg)
        server.quit()
        print("✉️ Email enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

# GERA RELATÓRIO
def gerar_relatorio():
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("SELECT tipo_sangue, COUNT(*) FROM doacoes GROUP BY tipo_sangue")
    doacoes = cursor.fetchall()

    cursor.execute("SELECT tipo_sangue, COUNT(*) FROM requisicoes WHERE status='aprovada' GROUP BY tipo_sangue")
    aprovadas = dict(cursor.fetchall())

    cursor.execute("SELECT tipo_sangue, COUNT(*) FROM requisicoes WHERE status='rejeitada' GROUP BY tipo_sangue")
    rejeitadas = dict(cursor.fetchall())

    # PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, "Relatório Geral - Banco de Sangue", ln=True, align="C")

    pdf.set_font("Arial", '', 12)
    pdf.ln(10)
    pdf.cell(0, 10, "Estoque Atual por Tipo Sanguíneo:", ln=True)

    for tipo, qtd in doacoes:
        pdf.cell(0, 10, f"Tipo {tipo}: {qtd} bolsas", ln=True)

        # ALERTAS SE ABAIXO DE 3 UNIDADES
        if qtd < 3:
            enviar_email(tipo, qtd)
            simular_sms(tipo, qtd)

    pdf.ln(10)
    pdf.cell(0, 10, "Resumo de Requisições:", ln=True)
    for tipo in set(list(aprovadas.keys()) + list(rejeitadas.keys())):
        aprov = aprovadas.get(tipo, 0)
        rejei = rejeitadas.get(tipo, 0)
        pdf.cell(0, 10, f"Tipo {tipo}: {aprov} aprovadas, {rejei} rejeitadas", ln=True)

    # Salva o relatório
    nome_arquivo = f"relatorio_banco_{datetime.datetime.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
    pdf.output(nome_arquivo)
    conn.close()

    # Notificação interna
    messagebox.showinfo("Relatório Gerado", f"Relatório salvo como {nome_arquivo}")

# Roda direto
if __name__ == "__main__":
    gerar_relatorio()
