# %% Configurações e Imports
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import bcrypt
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from fpdf import FPDF
import logging
import random
import json
import os
from PIL import Image, ImageTk

# Configurações iniciais
DB_NAME = 'blood_bank.db'
logging.basicConfig(filename='system.log', level=logging.INFO)

# %% Classe Principal
class BloodBankSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Hemolife Pro - Gestão Inteligente de Banco de Sangue")
        self.root.geometry("1400x900")
        self.style = ttk.Style()
        self.configure_styles()
        
        # Configurações de e-mail 
        self.email_config = {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'email': 'rosasomaquesendje@gmail.com',
            'password': 'password'
        }
        
        self.conn = sqlite3.connect(DB_NAME)
        self.create_tables()
        self.current_user = None
        self.alerts = []
        
        self.show_login_screen()
    
    def configure_styles(self):
        """Configura os estilos visuais do sistema"""
        self.style.theme_use('clam')
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('TLabel', background='#f5f5f5', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=6)
        self.style.configure('Primary.TButton', foreground='white', background='#d90429')
        self.style.configure('Secondary.TButton', foreground='white', background='#ef233c')
        self.style.configure('Success.TButton', foreground='white', background='#28a745')
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'), padding=[10, 5])
    
    def create_tables(self):
        """Cria as tabelas no banco de dados"""
        cursor = self.conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'technician')),
                email TEXT,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )''')
        
        # Tabela de tipos sanguíneos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blood_types (
                type TEXT PRIMARY KEY,
                min_stock INTEGER NOT NULL,
                description TEXT
            )''')
        
        # Tabela de estoque
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_date TEXT NOT NULL,
                expiration_date TEXT NOT NULL,
                donor_id TEXT,
                FOREIGN KEY (blood_type) REFERENCES blood_types(type)
            )''')
        
        # Tabela de requisições
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                requesting_doctor INTEGER NOT NULL,
                request_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
                response_date TEXT,
                responding_staff INTEGER,
                urgency TEXT CHECK(urgency IN ('Normal', 'Urgente', 'Emergência')),
                patient_info TEXT,
                FOREIGN KEY (blood_type) REFERENCES blood_types(type),
                FOREIGN KEY (requesting_doctor) REFERENCES users(id),
                FOREIGN KEY (responding_staff) REFERENCES users(id)
            )''')
        
        # Tabela de alertas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                recipient_id INTEGER NOT NULL,
                sent_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('sent', 'read')),
                FOREIGN KEY (recipient_id) REFERENCES users(id)
            )''')
        
        # Tabela de doações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_name TEXT NOT NULL,
                donor_cpf TEXT,
                donor_blood_type TEXT NOT NULL,
                donation_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                next_donation_date TEXT,
                FOREIGN KEY (donor_blood_type) REFERENCES blood_types(type)
            )''')
        
        # Inserir dados iniciais
        if not cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            self.create_initial_data()
        
        self.conn.commit()
    
    def create_initial_data(self):
        """Popula o banco com dados iniciais"""
        cursor = self.conn.cursor()
        
        # Usuários padrão
        users = [
            ('Admin', 'admin', self.hash_password('admin123'), 'admin', 'admin@hospital.com'),
            ('Dr. Silva', 'doctor', self.hash_password('doctor123'), 'doctor', 'doctor@hospital.com'),
            ('Técnico', 'tech', self.hash_password('tech123'), 'technician', 'tech@hospital.com')
        ]
        
        cursor.executemany(
            "INSERT INTO users (name, username, password, role, email) VALUES (?, ?, ?, ?, ?)",
            users
        )
        
        # Tipos sanguíneos
        blood_types = [
            ('A+', 30, 'Tipo A Positivo'),
            ('A-', 20, 'Tipo A Negativo'),
            ('B+', 25, 'Tipo B Positivo'),
            ('B-', 18, 'Tipo B Negativo'),
            ('O+', 40, 'Tipo O Positivo'),
            ('O-', 35, 'Tipo O Negativo'),
            ('AB+', 15, 'Tipo AB Positivo'),
            ('AB-', 10, 'Tipo AB Negativo')
        ]
        
        cursor.executemany(
            "INSERT INTO blood_types (type, min_stock, description) VALUES (?, ?, ?)",
            blood_types
        )
        
        # Inserir dados de estoque de exemplo
        today = datetime.now()
        for blood_type, _, _ in blood_types:
            for _ in range(3):
                expiration_date = today + timedelta(days=random.randint(30, 60))
                cursor.execute(
                    "INSERT INTO stock (blood_type, quantity, entry_date, expiration_date) VALUES (?, ?, ?, ?)",
                    (blood_type, random.randint(5, 15), today.isoformat(), expiration_date.isoformat())
                )
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Gera hash seguro da senha usando bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, hashed_password, input_password):
        """Verifica se a senha está correta"""
        return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def show_login_screen(self):
        """Exibe a tela de login"""
        self.clear_screen()
        
        login_frame = ttk.Frame(self.root, padding=30)
        login_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Logo e título
        ttk.Label(login_frame, text="🩸 HEMOLIFE PRO", font=('Arial', 24, 'bold'), 
                 foreground='#d90429').grid(row=0, column=0, columnspan=2, pady=(0, 20))
        ttk.Label(login_frame, text="Sistema Inteligente de Gestão de Banco de Sangue", 
                 font=('Arial', 12)).grid(row=1, column=0, columnspan=2, pady=(0, 30))
        
        # Campos de login
        ttk.Label(login_frame, text="Usuário:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Senha:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="•")
        self.password_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Botão de login
        login_btn = ttk.Button(login_frame, text="Acessar", style='Primary.TButton',
                              command=self.authenticate)
        login_btn.grid(row=4, column=0, columnspan=2, pady=20, ipadx=20, ipady=5)
        
        # Botão de recuperação de senha
        ttk.Button(login_frame, text="Esqueci minha senha", style='TButton',
                  command=self.show_password_recovery).grid(row=5, column=0, columnspan=2)
        
        self.username_entry.focus()
    
    def show_password_recovery(self):
        """Mostra diálogo para recuperação de senha"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Recuperação de Senha")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Digite seu e-mail cadastrado:", font=('Arial', 11)).pack(pady=10)
        
        email_entry = ttk.Entry(dialog, font=('Arial', 11), width=30)
        email_entry.pack(pady=5)
        
        def send_recovery():
            email = email_entry.get()
            if not email:
                messagebox.showerror("Erro", "Por favor, digite seu e-mail!")
                return
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT username, password FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            
            if user:
                try:
                    # Em um sistema real, você enviaria um e-mail com um link para redefinir a senha
                    # Aqui estamos apenas simulando
                    msg = EmailMessage()
                    msg['Subject'] = 'Recuperação de Senha - Hemolife Pro'
                    msg['From'] = self.email_config['email']
                    msg['To'] = email
                    msg.set_content(
                        f"Olá,\n\nVocê solicitou a recuperação de senha.\n"
                        f"Usuário: {user[0]}\n"
                        f"Por segurança, não enviamos senhas por e-mail.\n"
                        f"Entre em contato com o administrador para redefinir sua senha.\n\n"
                        f"Atenciosamente,\nEquipe Hemolife Pro"
                    )
                    
                    with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                        server.starttls()
                        server.login(self.email_config['email'], self.email_config['password'])
                        server.send_message(msg)
                    
                    messagebox.showinfo("Sucesso", "Instruções de recuperação enviadas para seu e-mail!")
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao enviar e-mail: {str(e)}")
            else:
                messagebox.showerror("Erro", "E-mail não encontrado no sistema!")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        
        ttk.Button(btn_frame, text="Enviar", style='Primary.TButton', command=send_recovery).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def authenticate(self):
        """Autentica o usuário"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Erro", "Por favor, preencha todos os campos!")
            return
        
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, role, password, is_active FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if user and user[4] == 0:
            messagebox.showerror("Erro", "Esta conta está desativada. Contate o administrador.")
            return
        
        if user and self.verify_password(user[3], password):
            self.current_user = {
                'id': user[0],
                'name': user[1],
                'role': user[2]
            }
            
            # Atualizar último login
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user[0])
                )
            self.conn.commit()
            
            self.log_activity(f"Login realizado por {user[1]}")
            self.load_alerts()
            self.show_main_interface()
        else:
            messagebox.showerror("Erro", "Credenciais inválidas!")
            self.log_activity(f"Tentativa de login falhou para usuário {username}")
    
    def load_alerts(self):
        """Carrega alertas não lidos do usuário atual"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, type, message, sent_date 
            FROM alerts 
            WHERE recipient_id = ? AND status = 'sent'
            ORDER BY sent_date DESC
        ''', (self.current_user['id'],))
        
        self.alerts = []
        for alert in cursor.fetchall():
            self.alerts.append({
                'id': alert[0],
                'type': alert[1],
                'message': alert[2],
                'date': alert[3]
            })
    
    def show_main_interface(self):
        """Exibe a interface principal conforme o perfil do usuário"""
        self.clear_screen()
        
        # Barra superior
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_bar, 
                 text=f"🩸 HEMOLIFE PRO | {self.current_user['name']} ({self.current_user['role'].title()})", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        # Botão de notificações
        alert_count = len(self.alerts)
        alert_text = f"🔔 {alert_count}" if alert_count > 0 else "🔔"
        self.alert_btn = ttk.Button(top_bar, text=alert_text, style='Primary.TButton' if alert_count > 0 else 'TButton',
                                  command=self.show_alerts)
        self.alert_btn.pack(side=tk.RIGHT, padx=5)
        
        logout_btn = ttk.Button(top_bar, text="Sair", style='Secondary.TButton',
                              command=self.show_login_screen)
        logout_btn.pack(side=tk.RIGHT)
        
        # Notebook (abas)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Criar abas conforme o perfil
        self.create_dashboard_tab()
        self.create_stock_tab()
        
        if self.current_user['role'] in ['admin', 'technician']:
            self.create_requests_tab()
            self.create_donations_tab()
        
        if self.current_user['role'] == 'doctor':
            self.create_doctor_tab()
        
        if self.current_user['role'] == 'admin':
            self.create_admin_tab()
            self.create_analytics_tab()
            self.create_chatbot_tab()
        
        # Verificar estoque baixo
        self.check_low_stock()
    
    def create_dashboard_tab(self):
        """Cria a aba de dashboard com resumo do sistema"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Dashboard")
        
        # Frame principal com scroll
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Resumo do estoque
        summary_frame = ttk.LabelFrame(scrollable_frame, text="Resumo do Estoque", padding=15)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock 
            FROM blood_types b
            LEFT JOIN stock s ON b.type = s.blood_type
            GROUP BY b.type
            ORDER BY b.type
        ''')
        
        stock_data = cursor.fetchall()
        
        # Gráfico de barras do estoque
        fig = plt.Figure(figsize=(10, 4), dpi=100)
        ax = fig.add_subplot(111)
        
        types = [row[0] for row in stock_data]
        quantities = [row[1] for row in stock_data]
        min_stocks = [row[2] for row in stock_data]
        
        ax.bar(types, quantities, color='#d90429', label='Estoque Atual')
        ax.plot(types, min_stocks, color='#ef233c', marker='o', linestyle='--', label='Estoque Mínimo')
        
        ax.set_title('Níveis de Estoque por Tipo Sanguíneo')
        ax.set_xlabel('Tipo Sanguíneo')
        ax.set_ylabel('Quantidade (unidades)')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        
        canvas_graph = FigureCanvasTkAgg(fig, summary_frame)
        canvas_graph.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Cards de resumo
        metrics_frame = ttk.Frame(scrollable_frame)
        metrics_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Total em estoque
        total_stock = sum(quantities)
        self.create_metric_card(metrics_frame, "Estoque Total", f"{total_stock} unidades", 0)
        
        # Requisições pendentes
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
        pending_requests = cursor.fetchone()[0]
        self.create_metric_card(metrics_frame, "Requisições Pendentes", str(pending_requests), 1)
        
        # Doações recentes
        cursor.execute("SELECT COUNT(*) FROM donations WHERE date(donation_date) = date('now')")
        today_donations = cursor.fetchone()[0]
        self.create_metric_card(metrics_frame, "Doações Hoje", str(today_donations), 2)
        
        # Alertas
        low_stock_types = sum(1 for row in stock_data if row[1] < row[2])
        self.create_metric_card(metrics_frame, "Tipos com Estoque Baixo", str(low_stock_types), 3)
        
        # Últimas requisições
        requests_frame = ttk.LabelFrame(scrollable_frame, text="Últimas Requisições", padding=15)
        requests_frame.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)
        
        columns = ('id', 'type', 'qty', 'doctor', 'date', 'status')
        self.dashboard_requests_tree = ttk.Treeview(requests_frame, columns=columns, show='headings', height=6)
        
        self.dashboard_requests_tree.heading('id', text='ID')
        self.dashboard_requests_tree.heading('type', text='Tipo')
        self.dashboard_requests_tree.heading('qty', text='Qtd')
        self.dashboard_requests_tree.heading('doctor', text='Médico')
        self.dashboard_requests_tree.heading('date', text='Data')
        self.dashboard_requests_tree.heading('status', text='Status')
        
        self.dashboard_requests_tree.column('id', width=50, anchor='center')
        self.dashboard_requests_tree.column('type', width=70, anchor='center')
        self.dashboard_requests_tree.column('qty', width=50, anchor='center')
        self.dashboard_requests_tree.column('doctor', width=150)
        self.dashboard_requests_tree.column('date', width=120)
        self.dashboard_requests_tree.column('status', width=100, anchor='center')
        
        self.dashboard_requests_tree.pack(fill=tk.BOTH, expand=True)
        
        # Preencher com as últimas 10 requisições
        cursor.execute('''
            SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status
            FROM requests r
            JOIN users u ON r.requesting_doctor = u.id
            ORDER BY r.request_date DESC
            LIMIT 10
        ''')
        
        for row in cursor.fetchall():
            status_text = {
                'pending': '⏳ Pendente',
                'approved': '✅ Aprovada',
                'rejected': '❌ Rejeitada'
            }.get(row[5], row[5])
            
            self.dashboard_requests_tree.insert('', 'end', values=row[:5] + (status_text,))
    
    def create_metric_card(self, parent, title, value, column):
        """Cria um card de métrica para o dashboard"""
        card = ttk.Frame(parent, relief='groove', borderwidth=2)
        card.grid(row=0, column=column, padx=5, pady=5, sticky='nsew')
        parent.columnconfigure(column, weight=1)
        
        ttk.Label(card, text=title, font=('Arial', 10, 'bold')).pack(pady=(5, 0))
        ttk.Label(card, text=value, font=('Arial', 14, 'bold'), foreground='#d90429').pack(pady=(0, 5))
        
        # Estilo baseado no valor
        if title == "Tipos com Estoque Baixo" and int(value) > 0:
            card.configure(relief='raised', style='Secondary.TFrame')
    
    def create_stock_tab(self):
        """Cria a aba de estoque"""
        stock_tab = ttk.Frame(self.notebook)
        self.notebook.add(stock_tab, text="📦 Estoque")
        
        # Frame de controle
        control_frame = ttk.Frame(stock_tab, padding=10)
        control_frame.pack(fill=tk.X)
        
        # Combo box para tipos sanguíneos
        ttk.Label(control_frame, text="Tipo Sanguíneo:").grid(row=0, column=0, padx=5)
        self.blood_type_combo = ttk.Combobox(control_frame, state="readonly")
        self.blood_type_combo.grid(row=0, column=1, padx=5)
        
        # Botão para adicionar estoque (apenas para técnicos e admin)
        if self.current_user['role'] in ['admin', 'technician']:
            add_btn = ttk.Button(control_frame, text="Adicionar Estoque", style='Primary.TButton',
                               command=self.show_add_stock_dialog)
            add_btn.grid(row=0, column=2, padx=10)
            
            # Botão para gerar relatório
            report_btn = ttk.Button(control_frame, text="Gerar Relatório", style='Success.TButton',
                                  command=self.generate_stock_report)
            report_btn.grid(row=0, column=3, padx=5)
        
        # Atualizar lista de tipos
        self.update_blood_types()
        
        # Treeview para exibir estoque
        self.stock_tree = ttk.Treeview(stock_tab, columns=('type', 'quantity', 'min', 'status'), show='headings')
        self.stock_tree.heading('type', text='Tipo')
        self.stock_tree.heading('quantity', text='Quantidade')
        self.stock_tree.heading('min', text='Mínimo')
        self.stock_tree.heading('status', text='Status')
        self.stock_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurar tags para cores
        self.stock_tree.tag_configure('low', background='#fff3cd')  # Amarelo para estoque baixo
        
        # Atualizar dados
        self.update_stock_display()
    
    def show_add_stock_dialog(self):
        """Mostra diálogo para adicionar estoque"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar ao Estoque")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Tipo Sanguíneo:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        type_combo = ttk.Combobox(dialog, state="readonly")
        type_combo.grid(row=0, column=1, padx=10, pady=10, sticky='we')
        
        # Preencher tipos sanguíneos
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        type_combo['values'] = types
        if types:
            type_combo.current(0)
        
        ttk.Label(dialog, text="Quantidade:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        qty_entry = ttk.Entry(dialog)
        qty_entry.grid(row=1, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Data de Validade:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        expiry_entry = ttk.Entry(dialog)
        expiry_entry.grid(row=2, column=1, padx=10, pady=10, sticky='we')
        expiry_entry.insert(0, (datetime.now() + timedelta(days=42)).strftime('%d/%m/%Y'))
        
        ttk.Label(dialog, text="ID do Doador (opcional):").grid(row=3, column=0, padx=10, pady=10, sticky='e')
        donor_entry = ttk.Entry(dialog)
        donor_entry.grid(row=3, column=1, padx=10, pady=10, sticky='we')
        
        def save_stock():
            blood_type = type_combo.get()
            quantity = qty_entry.get()
            expiry = expiry_entry.get()
            donor_id = donor_entry.get()
            
            if not blood_type or not quantity or not expiry:
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return
            
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
                
                # Converter data para formato ISO
                expiry_date = datetime.strptime(expiry, '%d/%m/%Y').date().isoformat()
                
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO stock (blood_type, quantity, entry_date, expiration_date, donor_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (blood_type, quantity, datetime.now().isoformat(), expiry_date, donor_id or None))
                
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Estoque adicionado com sucesso!")
                self.update_stock_display()
                dialog.destroy()
                
                # Verificar se estoque saiu do nível crítico
                self.check_stock_levels(blood_type)
                
            except ValueError:
                messagebox.showerror("Erro", "Quantidade deve ser um número positivo!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao adicionar estoque: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_stock).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_blood_types(self):
        """Atualiza a lista de tipos sanguíneos no combobox"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        self.blood_type_combo['values'] = types
        if types:
            self.blood_type_combo.current(0)
    
    def update_stock_display(self):
        """Atualiza a exibição do estoque"""
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock 
            FROM blood_types b
            LEFT JOIN stock s ON b.type = s.blood_type
            GROUP BY b.type
            ORDER BY b.type
        ''')
        
        for row in cursor.fetchall():
            stock = row[1]
            min_stock = row[2]
            
            if stock < min_stock:
                status = f"⚠️ Baixo (mín: {min_stock})"
                tag = 'low'
            else:
                status = "✅ OK"
                tag = ''
            
            self.stock_tree.insert('', 'end', values=(row[0], stock, min_stock, status), tags=(tag,))
    
    def generate_stock_report(self):
        """Gera relatório PDF do estoque atual"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            pdf.cell(0, 10, 'Relatório de Estoque de Sangue', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Emitido em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            pdf.cell(0, 10, f'Emitido por: {self.current_user["name"]}', 0, 1, 'C')
            pdf.ln(10)
            
            # Dados do estoque
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Níveis de Estoque por Tipo Sanguíneo', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Cabeçalho da tabela
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(40, 10, 'Tipo Sanguíneo', 1, 0, 'C', 1)
            pdf.cell(40, 10, 'Quantidade', 1, 0, 'C', 1)
            pdf.cell(40, 10, 'Estoque Mínimo', 1, 0, 'C', 1)
            pdf.cell(70, 10, 'Status', 1, 1, 'C', 1)
            
            pdf.set_fill_color(255, 255, 255)
            
            # Obter dados do estoque
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock 
                FROM blood_types b
                LEFT JOIN stock s ON b.type = s.blood_type
                GROUP BY b.type
                ORDER BY b.type
            ''')
            
            for row in cursor.fetchall():
                blood_type = row[0]
                stock = row[1]
                min_stock = row[2]
                
                if stock < min_stock:
                    status = f"ESTOQUE BAIXO (faltam {min_stock - stock} unidades)"
                    pdf.set_text_color(255, 0, 0)  # Vermelho
                else:
                    status = "OK"
                    pdf.set_text_color(0, 0, 0)  # Preto
                
                pdf.cell(40, 10, blood_type, 1, 0, 'C')
                pdf.cell(40, 10, str(stock), 1, 0, 'C')
                pdf.cell(40, 10, str(min_stock), 1, 0, 'C')
                pdf.cell(70, 10, status, 1, 1, 'C')
            
            # Itens próximos a vencer
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, 'Itens Próximos do Vencimento (7 dias)', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Cabeçalho da tabela
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(40, 10, 'Tipo Sanguíneo', 1, 0, 'C', 1)
            pdf.cell(40, 10, 'Quantidade', 1, 0, 'C', 1)
            pdf.cell(40, 10, 'Data Validade', 1, 0, 'C', 1)
            pdf.cell(70, 10, 'Dias Restantes', 1, 1, 'C', 1)
            
            pdf.set_fill_color(255, 255, 255)
            
            # Obter itens próximos a vencer
            cursor.execute('''
                SELECT blood_type, quantity, expiration_date 
                FROM stock 
                WHERE date(expiration_date) BETWEEN date('now') AND date('now', '+7 days')
                ORDER BY expiration_date
            ''')
            
            today = datetime.now().date()
            has_expiring = False
            
            for row in cursor.fetchall():
                has_expiring = True
                expiry_date = datetime.strptime(row[2], '%Y-%m-%d').date()
                days_left = (expiry_date - today).days
                
                pdf.cell(40, 10, row[0], 1, 0, 'C')
                pdf.cell(40, 10, str(row[1]), 1, 0, 'C')
                pdf.cell(40, 10, expiry_date.strftime('%d/%m/%Y'), 1, 0, 'C')
                
                if days_left <= 0:
                    pdf.set_text_color(255, 0, 0)
                    status = "VENCIDO"
                else:
                    pdf.set_text_color(255, 165, 0)  # Laranja
                    status = f"{days_left} dias"
                
                pdf.cell(70, 10, status, 1, 1, 'C')
                pdf.set_text_color(0, 0, 0)
            
            if not has_expiring:
                pdf.cell(0, 10, 'Nenhum item próximo do vencimento', 1, 1, 'C')
            
            # Salvar PDF
            filename = f"relatorio_estoque_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            pdf.output(filename)
            
            messagebox.showinfo("Sucesso", f"Relatório gerado com sucesso:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
            self.log_activity(f"Erro ao gerar relatório de estoque: {str(e)}", level='ERROR')
    
    def create_requests_tab(self):
        """Cria a aba para gerenciar requisições (técnicos e admin)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📋 Requisições")
        
        # Frame de controle
        control_frame = ttk.Frame(tab, padding=10)
        control_frame.pack(fill=tk.X)
        
        # Filtros
        ttk.Label(control_frame, text="Filtrar:").grid(row=0, column=0, padx=5)
        self.filter_combo = ttk.Combobox(control_frame, values=["Todas", "Pendentes", "Aprovadas", "Rejeitadas"], state="readonly")
        self.filter_combo.current(0)
        self.filter_combo.grid(row=0, column=1, padx=5)
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self.update_requests_display())
        
        # Busca por médico
        ttk.Label(control_frame, text="Buscar Médico:").grid(row=0, column=2, padx=5)
        self.doctor_search_entry = ttk.Entry(control_frame)
        self.doctor_search_entry.grid(row=0, column=3, padx=5)
        self.doctor_search_entry.bind('<KeyRelease>', lambda e: self.update_requests_display())
        
        # Treeview para requisições
        self.requests_tree = ttk.Treeview(tab, columns=('id', 'type', 'qty', 'doctor', 'date', 'status', 'urgency'), show='headings')
        self.requests_tree.heading('id', text='ID')
        self.requests_tree.heading('type', text='Tipo Sanguíneo')
        self.requests_tree.heading('qty', text='Quantidade')
        self.requests_tree.heading('doctor', text='Médico')
        self.requests_tree.heading('date', text='Data')
        self.requests_tree.heading('status', text='Status')
        self.requests_tree.heading('urgency', text='Urgência')
        
        self.requests_tree.column('id', width=50, anchor='center')
        self.requests_tree.column('type', width=80, anchor='center')
        self.requests_tree.column('qty', width=60, anchor='center')
        self.requests_tree.column('doctor', width=150)
        self.requests_tree.column('date', width=120)
        self.requests_tree.column('status', width=100, anchor='center')
        self.requests_tree.column('urgency', width=80, anchor='center')
        
        self.requests_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de aprovação
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(action_frame, text="Aprovar", style='Primary.TButton',
                  command=self.approve_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Rejeitar", style='Secondary.TButton',
                  command=self.reject_request).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Visualizar", style='Success.TButton',
                  command=self.view_request_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Gerar Relatório", style='Primary.TButton',
                  command=self.generate_request_report).pack(side=tk.RIGHT, padx=5)
        
        self.update_requests_display()
    
    def update_requests_display(self):
        """Atualiza a lista de requisições"""
        for item in self.requests_tree.get_children():
            self.requests_tree.delete(item)
        
        cursor = self.conn.cursor()
        filter_status = self.filter_combo.get()
        doctor_search = self.doctor_search_entry.get().strip()
        
        query = '''
            SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status, r.urgency
            FROM requests r
            JOIN users u ON r.requesting_doctor = u.id
        '''
        
        conditions = []
        params = []
        
        if filter_status != "Todas":
            status_map = {"Pendentes": "pending", "Aprovadas": "approved", "Rejeitadas": "rejected"}
            conditions.append("r.status = ?")
            params.append(status_map[filter_status])
        
        if doctor_search:
            conditions.append("u.name LIKE ?")
            params.append(f"%{doctor_search}%")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY r.request_date DESC"
        
        cursor.execute(query, params)
        
        for row in cursor.fetchall():
            status_text = {
                'pending': '⏳ Pendente',
                'approved': '✅ Aprovada',
                'rejected': '❌ Rejeitada'
            }.get(row[5], row[5])
            
            urgency_text = row[6] or "Normal"
            if urgency_text == "Emergência":
                urgency_text = "🚨 " + urgency_text
            elif urgency_text == "Urgente":
                urgency_text = "⚠️ " + urgency_text
            
            self.requests_tree.insert('', 'end', values=row[:5] + (status_text, urgency_text), 
                                    tags=(row[5],))
        
        self.requests_tree.tag_configure('pending', background='#fff3cd')
        self.requests_tree.tag_configure('approved', background='#d4edda')
        self.requests_tree.tag_configure('rejected', background='#f8d7da')
    
    def view_request_details(self):
        """Mostra detalhes da requisição selecionada"""
        selected = self.requests_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma requisição para visualizar!")
            return
        
        request_id = self.requests_tree.item(selected[0])['values'][0]
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status, 
                   r.urgency, r.patient_info, r.response_date, u2.name
            FROM requests r
            JOIN users u ON r.requesting_doctor = u.id
            LEFT JOIN users u2 ON r.responding_staff = u2.id
            WHERE r.id = ?
        ''', (request_id,))
        
        request_data = cursor.fetchone()
        
        if not request_data:
            messagebox.showerror("Erro", "Requisição não encontrada!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Detalhes da Requisição #{request_id}")
        dialog.geometry("500x400")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campos de detalhes
        fields = [
            ("ID:", request_data[0]),
            ("Tipo Sanguíneo:", request_data[1]),
            ("Quantidade:", request_data[2]),
            ("Médico Solicitante:", request_data[3]),
            ("Data da Requisição:", request_data[4]),
            ("Status:", {
                'pending': 'Pendente',
                'approved': 'Aprovada',
                'rejected': 'Rejeitada'
            }.get(request_data[5], request_data[5])),
            ("Urgência:", request_data[6] or "Normal"),
            ("Informações do Paciente:", request_data[7] or "Não informado"),
            ("Data da Resposta:", request_data[8] or "N/A"),
            ("Responsável pela Resposta:", request_data[9] or "N/A")
        ]
        
        for i, (label, value) in enumerate(fields):
            ttk.Label(main_frame, text=label, font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='e', padx=5, pady=2)
            ttk.Label(main_frame, text=value).grid(row=i, column=1, sticky='w', padx=5, pady=2)
        
        # Botão para fechar
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Fechar", command=dialog.destroy).pack()
    
    def approve_request(self):
        """Aprova a requisição selecionada"""
        selected = self.requests_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma requisição para aprovar!")
            return
        
        request_id = self.requests_tree.item(selected[0])['values'][0]
        
        try:
            cursor = self.conn.cursor()
            
            # Obter dados da requisição
            cursor.execute('''
                SELECT blood_type, quantity FROM requests WHERE id = ? AND status = 'pending'
            ''', (request_id,))
            request_data = cursor.fetchone()
            
            if not request_data:
                messagebox.showerror("Erro", "Requisição já processada ou não encontrada!")
                return
            
            blood_type, quantity = request_data
            
            # Verificar estoque
            cursor.execute('''
                SELECT SUM(quantity) FROM stock WHERE blood_type = ?
            ''', (blood_type,))
            current_stock = cursor.fetchone()[0] or 0
            
            if current_stock < quantity:
                messagebox.showerror("Erro", f"Estoque insuficiente! Disponível: {current_stock}")
                return
            
            # Atualizar requisição
            cursor.execute('''
                UPDATE requests 
                SET status = 'approved', 
                    responding_staff = ?,
                    response_date = ?
                WHERE id = ?
            ''', (self.current_user['id'], datetime.now().isoformat(), request_id))
            
            # Remover do estoque
            cursor.execute('''
                INSERT INTO stock (blood_type, quantity, entry_date, expiration_date)
                VALUES (?, ?, ?, ?)
            ''', (blood_type, -quantity, datetime.now().isoformat(), datetime.now().isoformat()))
            
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Requisição aprovada e estoque atualizado!")
            self.update_requests_display()
            self.update_stock_display()
            
            # Enviar notificação ao médico
            self.notify_doctor(request_id, approved=True)
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Falha ao aprovar requisição: {str(e)}")
    
    def reject_request(self):
        """Rejeita a requisição selecionada"""
        selected = self.requests_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma requisição para rejeitar!")
            return
        
        request_id = self.requests_tree.item(selected[0])['values'][0]
        
        # Pedir motivo da rejeição
        dialog = tk.Toplevel(self.root)
        dialog.title("Motivo da Rejeição")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="Informe o motivo da rejeição:", font=('Arial', 11)).pack(pady=10)
        
        reason_text = scrolledtext.ScrolledText(dialog, width=40, height=5)
        reason_text.pack(pady=5, padx=10)
        
        def confirm_reject():
            reason = reason_text.get("1.0", tk.END).strip()
            if not reason:
                messagebox.showerror("Erro", "Por favor, informe o motivo da rejeição!")
                return
            
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE requests 
                    SET status = 'rejected', 
                        responding_staff = ?,
                        response_date = ?,
                        patient_info = COALESCE(patient_info, '') || '\nMotivo da rejeição: ' || ?
                    WHERE id = ?
                ''', (self.current_user['id'], datetime.now().isoformat(), reason, request_id))
                
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Requisição rejeitada!")
                dialog.destroy()
                self.update_requests_display()
                
                # Enviar notificação ao médico
                self.notify_doctor(request_id, approved=False, reason=reason)
                
            except sqlite3.Error as e:
                messagebox.showerror("Erro", f"Falha ao rejeitar requisição: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Confirmar", style='Secondary.TButton', command=confirm_reject).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def notify_doctor(self, request_id, approved, reason=None):
        """Envia notificação ao médico sobre a requisição"""
        cursor = self.conn.cursor()
        
        # Obter detalhes da requisição e médico
        cursor.execute('''
            SELECT u.name, u.email, r.blood_type, r.quantity
            FROM requests r
            JOIN users u ON r.requesting_doctor = u.id
            WHERE r.id = ?
        ''', (request_id,))
        
        request_data = cursor.fetchone()
        if not request_data:
            return
        
        doctor_name, doctor_email, blood_type, quantity = request_data
        
        # Criar mensagem
        if approved:
            subject = f"Requisição #{request_id} Aprovada"
            message = (
                f"Olá Dr(a). {doctor_name},\n\n"
                f"Sua requisição de {quantity} unidades de {blood_type} foi aprovada.\n"
                f"ID da Requisição: {request_id}\n"
                f"Data da Resposta: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Atenciosamente,\nEquipe Hemolife Pro"
            )
        else:
            subject = f"Requisição #{request_id} Rejeitada"
            message = (
                f"Olá Dr(a). {doctor_name},\n\n"
                f"Sua requisição de {quantity} unidades de {blood_type} foi rejeitada.\n"
                f"Motivo: {reason or 'Não informado'}\n"
                f"ID da Requisição: {request_id}\n"
                f"Data da Resposta: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
                f"Atenciosamente,\nEquipe Hemolife Pro"
            )
        
        # Enviar e-mail (simulado)
        if doctor_email:
            try:
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = self.email_config['email']
                msg['To'] = doctor_email
                msg.set_content(message)
                
                with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                    server.starttls()
                    server.login(self.email_config['email'], self.email_config['password'])
                    server.send_message(msg)
                
                self.log_activity(f"Notificação enviada para {doctor_name} sobre requisição {request_id}")
            except Exception as e:
                self.log_activity(f"Falha ao enviar e-mail para {doctor_email}: {str(e)}", level='ERROR')
        
        # Registrar alerta no sistema
        cursor.execute('''
            INSERT INTO alerts (type, message, recipient_id, sent_date, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('request_update', message, self.current_user['id'], datetime.now().isoformat(), 'sent'))
        
        self.conn.commit()
    
    def notify_staff_new_request(self):
        """Notifica a equipe sobre nova requisição pendente"""
        cursor = self.conn.cursor()
        
        # Obter técnicos e administradores
        cursor.execute("SELECT id, name, email FROM users WHERE role IN ('admin', 'technician') AND is_active = 1")
        staff_members = cursor.fetchall()
        
        if not staff_members:
            return
        
        # Criar mensagem
        message = (
            f"Nova requisição de sangue pendente de aprovação.\n"
            f"Por favor, acesse o sistema para revisar.\n\n"
            f"Atenciosamente,\nEquipe Hemolife Pro"
        )
        
        # Enviar notificações
        for member_id, member_name, member_email in staff_members:
            # Registrar alerta no sistema
            cursor.execute('''
                INSERT INTO alerts (type, message, recipient_id, sent_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', ('new_request', message, member_id, datetime.now().isoformat(), 'sent'))
            
            # Enviar e-mail (simulado)
            if member_email:
                try:
                    msg = EmailMessage()
                    msg['Subject'] = "Nova Requisição de Sangue Pendente"
                    msg['From'] = self.email_config['email']
                    msg['To'] = member_email
                    msg.set_content(
                        f"Olá {member_name},\n\n{message}"
                    )
                    
                    with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                        server.starttls()
                        server.login(self.email_config['email'], self.email_config['password'])
                        server.send_message(msg)
                    
                    self.log_activity(f"Notificação de nova requisição enviada para {member_name}")
                except Exception as e:
                    self.log_activity(f"Falha ao enviar e-mail para {member_email}: {str(e)}", level='ERROR')
        
        self.conn.commit()
    
    def create_doctor_tab(self):
        """Cria a aba específica para médicos"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🩺 Solicitar Sangue")
        
        # Formulário de requisição
        form_frame = ttk.Frame(tab, padding=20)
        form_frame.pack(fill=tk.X)
        
        ttk.Label(form_frame, text="Tipo Sanguíneo:", font=('Arial', 11)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.request_type_combo = ttk.Combobox(form_frame, state="readonly", font=('Arial', 11))
        self.request_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.update_blood_types_doctor()
        
        ttk.Label(form_frame, text="Quantidade:", font=('Arial', 11)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.request_qty_entry = ttk.Entry(form_frame, font=('Arial', 11))
        self.request_qty_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(form_frame, text="Urgência:", font=('Arial', 11)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.request_urgency_combo = ttk.Combobox(form_frame, values=["Normal", "Urgente", "Emergência"], state="readonly", font=('Arial', 11))
        self.request_urgency_combo.current(0)
        self.request_urgency_combo.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        ttk.Label(form_frame, text="Informações do Paciente:", font=('Arial', 11)).grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.patient_info_text = scrolledtext.ScrolledText(form_frame, width=40, height=4, font=('Arial', 11))
        self.patient_info_text.grid(row=3, column=1, padx=5, pady=5, sticky='we')
        
        submit_btn = ttk.Button(form_frame, text="Enviar Requisição", style='Primary.TButton',
                              command=self.submit_blood_request)
        submit_btn.grid(row=4, column=0, columnspan=2, pady=15)
        
        # Histórico de requisições do médico
        ttk.Label(tab, text="Minhas Requisições:", font=('Arial', 12, 'bold')).pack(pady=(10, 5))
        
        self.doctor_requests_tree = ttk.Treeview(tab, columns=('id', 'type', 'qty', 'date', 'status', 'urgency'), show='headings', height=8)
        self.doctor_requests_tree.heading('id', text='ID')
        self.doctor_requests_tree.heading('type', text='Tipo')
        self.doctor_requests_tree.heading('qty', text='Qtd')
        self.doctor_requests_tree.heading('date', text='Data')
        self.doctor_requests_tree.heading('status', text='Status')
        self.doctor_requests_tree.heading('urgency', text='Urgência')
        
        self.doctor_requests_tree.column('id', width=50, anchor='center')
        self.doctor_requests_tree.column('type', width=70, anchor='center')
        self.doctor_requests_tree.column('qty', width=50, anchor='center')
        self.doctor_requests_tree.column('date', width=120)
        self.doctor_requests_tree.column('status', width=100, anchor='center')
        self.doctor_requests_tree.column('urgency', width=80, anchor='center')
        
        self.doctor_requests_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.update_doctor_requests()
    
    def update_blood_types_doctor(self):
        """Atualiza a lista de tipos sanguíneos para médicos"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        self.request_type_combo['values'] = types
        if types:
            self.request_type_combo.current(0)
    
    def submit_blood_request(self):
        """Submete uma nova requisição de sangue"""
        blood_type = self.request_type_combo.get()
        quantity = self.request_qty_entry.get()
        urgency = self.request_urgency_combo.get()
        patient_info = self.patient_info_text.get("1.0", tk.END).strip()
        
        if not blood_type or not quantity:
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
            return
        
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Erro", "Quantidade deve ser um número positivo!")
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Verificar estoque atual
            cursor.execute('''
                SELECT SUM(quantity) FROM stock WHERE blood_type = ?
            ''', (blood_type,))
            current_stock = cursor.fetchone()[0] or 0
            
            if current_stock < quantity and urgency != "Emergência":
                messagebox.showwarning("Aviso", 
                    f"Estoque atual de {blood_type}: {current_stock}\n"
                    f"Sua requisição será enviada para aprovação.")
            
            # Inserir requisição
            cursor.execute('''
                INSERT INTO requests (blood_type, quantity, requesting_doctor, request_date, status, urgency, patient_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (blood_type, quantity, self.current_user['id'], datetime.now().isoformat(), 'pending', urgency, patient_info))
            
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", "Requisição enviada para aprovação!")
            self.update_doctor_requests()
            
            # Limpar formulário
            self.request_qty_entry.delete(0, tk.END)
            self.patient_info_text.delete("1.0", tk.END)
            
            # Enviar notificação aos técnicos/admins
            self.notify_staff_new_request()
            
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Falha ao enviar requisição: {str(e)}")
    
    def update_doctor_requests(self):
        """Atualiza a lista de requisições do médico"""
        for item in self.doctor_requests_tree.get_children():
            self.doctor_requests_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, blood_type, quantity, request_date, status, urgency
            FROM requests
            WHERE requesting_doctor = ?
            ORDER BY request_date DESC
        ''', (self.current_user['id'],))
        
        for row in cursor.fetchall():
            status_text = {
                'pending': '⏳ Pendente',
                'approved': '✅ Aprovada',
                'rejected': '❌ Rejeitada'
            }.get(row[4], row[4])
            
            urgency_text = row[5] or "Normal"
            if urgency_text == "Emergência":
                urgency_text = "🚨 " + urgency_text
            elif urgency_text == "Urgente":
                urgency_text = "⚠️ " + urgency_text
            
            self.doctor_requests_tree.insert('', 'end', values=row[:4] + (status_text, urgency_text))
    
    def create_donations_tab(self):
        """Cria a aba para gerenciar doações (técnicos e admin)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🩹 Doações")
        
        # Frame de controle
        control_frame = ttk.Frame(tab, padding=10)
        control_frame.pack(fill=tk.X)
        
        # Botões de ação
        ttk.Button(control_frame, text="Registrar Doação", style='Primary.TButton',
                  command=self.show_add_donation_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Gerar Relatório", style='Success.TButton',
                  command=self.generate_donation_report).pack(side=tk.LEFT, padx=5)
        
        # Filtros
        ttk.Label(control_frame, text="Filtrar por Tipo:").pack(side=tk.LEFT, padx=5)
        self.donation_filter_combo = ttk.Combobox(control_frame, state="readonly")
        self.donation_filter_combo.pack(side=tk.LEFT, padx=5)
        self.donation_filter_combo.bind("<<ComboboxSelected>>", lambda e: self.update_donations_display())
        
        # Preencher tipos sanguíneos
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        self.donation_filter_combo['values'] = ['Todos'] + types
        self.donation_filter_combo.current(0)
        
        # Treeview para doações
        self.donations_tree = ttk.Treeview(tab, columns=('id', 'name', 'cpf', 'type', 'date', 'qty', 'next'), show='headings')
        self.donations_tree.heading('id', text='ID')
        self.donations_tree.heading('name', text='Doador')
        self.donations_tree.heading('cpf', text='CPF')
        self.donations_tree.heading('type', text='Tipo')
        self.donations_tree.heading('date', text='Data')
        self.donations_tree.heading('qty', text='Qtd (ml)')
        self.donations_tree.heading('next', text='Próxima Doação')
        
        self.donations_tree.column('id', width=50, anchor='center')
        self.donations_tree.column('name', width=150)
        self.donations_tree.column('cpf', width=100)
        self.donations_tree.column('type', width=70, anchor='center')
        self.donations_tree.column('date', width=100)
        self.donations_tree.column('qty', width=70, anchor='center')
        self.donations_tree.column('next', width=100)
        
        self.donations_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Atualizar exibição
        self.update_donations_display()
    
    def show_add_donation_dialog(self):
        """Mostra diálogo para registrar nova doação"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Doação")
        dialog.geometry("500x400")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Campos do formulário
        fields = []
        
        ttk.Label(main_frame, text="Nome do Doador:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        name_entry = ttk.Entry(main_frame)
        name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='we')
        fields.append(('name', name_entry))
        
        ttk.Label(main_frame, text="CPF:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        cpf_entry = ttk.Entry(main_frame)
        cpf_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')
        fields.append(('cpf', cpf_entry))
        
        ttk.Label(main_frame, text="Tipo Sanguíneo:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        type_combo = ttk.Combobox(main_frame, state="readonly")
        type_combo.grid(row=2, column=1, padx=5, pady=5, sticky='we')
        
        # Preencher tipos sanguíneos
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        type_combo['values'] = types
        if types:
            type_combo.current(0)
        fields.append(('type', type_combo))
        
        ttk.Label(main_frame, text="Data da Doação:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        date_entry = ttk.Entry(main_frame)
        date_entry.insert(0, datetime.now().strftime('%d/%m/%Y'))
        date_entry.grid(row=3, column=1, padx=5, pady=5, sticky='we')
        fields.append(('date', date_entry))
        
        ttk.Label(main_frame, text="Quantidade (ml):").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        qty_entry = ttk.Entry(main_frame)
        qty_entry.insert(0, "450")  # Quantidade padrão de uma doação
        qty_entry.grid(row=4, column=1, padx=5, pady=5, sticky='we')
        fields.append(('qty', qty_entry))
        
        def save_donation():
            data = {field: entry.get() for field, entry in fields}
            
            # Validação
            if not all(data.values()):
                messagebox.showerror("Erro", "Preencha todos os campos!")
                return
            
            try:
                qty = int(data['qty'])
                if qty <= 0:
                    raise ValueError
                
                # Converter data para formato ISO
                donation_date = datetime.strptime(data['date'], '%d/%m/%Y').date().isoformat()
                next_donation_date = (datetime.strptime(data['date'], '%d/%m/%Y') + timedelta(days=90)).date().isoformat()
                
                cursor = self.conn.cursor()
                
                # Registrar doação
                cursor.execute('''
                    INSERT INTO donations (donor_name, donor_cpf, donor_blood_type, donation_date, quantity, next_donation_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (data['name'], data['cpf'], data['type'], donation_date, qty, next_donation_date))
                
                # Adicionar ao estoque
                cursor.execute('''
                    INSERT INTO stock (blood_type, quantity, entry_date, expiration_date, donor_id)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data['type'], qty, donation_date, (datetime.strptime(data['date'], '%d/%m/%Y') + timedelta(days=42)).date().isoformat(), 
                              f"{data['name']} (CPF: {data['cpf']})"))
                
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Doação registrada e estoque atualizado!")
                self.update_donations_display()
                self.update_stock_display()
                dialog.destroy()
                
                # Verificar se estoque saiu do nível crítico
                self.check_stock_levels(data['type'])
                
            except ValueError:
                messagebox.showerror("Erro", "Quantidade deve ser um número positivo!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao registrar doação: {str(e)}")
        
        # Frame de botões
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_donation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_donations_display(self):
        """Atualiza a lista de doações"""
        for item in self.donations_tree.get_children():
            self.donations_tree.delete(item)
        
        cursor = self.conn.cursor()
        blood_type = self.donation_filter_combo.get()
        
        if blood_type == 'Todos':
            cursor.execute('''
                SELECT id, donor_name, donor_cpf, donor_blood_type, donation_date, quantity, next_donation_date
                FROM donations
                ORDER BY donation_date DESC
            ''')
        else:
            cursor.execute('''
                SELECT id, donor_name, donor_cpf, donor_blood_type, donation_date, quantity, next_donation_date
                FROM donations
                WHERE donor_blood_type = ?
                ORDER BY donation_date DESC
            ''', (blood_type,))
        
        today = datetime.now().date()
        
        for row in cursor.fetchall():
            donation_date = datetime.strptime(row[4], '%Y-%m-%d').date()
            next_donation = datetime.strptime(row[6], '%Y-%m-%d').date() if row[6] else None
            
            # Verificar se já pode doar novamente
            if next_donation and next_donation <= today:
                next_text = "Pode doar"
                tags = ('can_donate',)
            else:
                next_text = row[6] if row[6] else "N/A"
                tags = ()
            
            self.donations_tree.insert('', 'end', values=(
                row[0], row[1], row[2], row[3], 
                donation_date.strftime('%d/%m/%Y'), 
                row[5], next_text
            ), tags=tags)
        
        self.donations_tree.tag_configure('can_donate', background='#d4edda')
    
    def generate_donation_report(self):
        """Gera relatório PDF das doações"""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            pdf.cell(0, 10, 'Relatório de Doações de Sangue', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Emitido em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            pdf.cell(0, 10, f'Emitido por: {self.current_user["name"]}', 0, 1, 'C')
            pdf.ln(10)
            
            # Filtro aplicado
            blood_type = self.donation_filter_combo.get()
            if blood_type != 'Todos':
                pdf.cell(0, 10, f'Filtro: Tipo Sanguíneo {blood_type}', 0, 1)
                pdf.ln(5)
            
            # Dados das doações
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Registro de Doações', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Cabeçalho da tabela
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(15, 10, 'ID', 1, 0, 'C', 1)
            pdf.cell(50, 10, 'Doador', 1, 0, 'C', 1)
            pdf.cell(30, 10, 'CPF', 1, 0, 'C', 1)
            pdf.cell(20, 10, 'Tipo', 1, 0, 'C', 1)
            pdf.cell(30, 10, 'Data', 1, 0, 'C', 1)
            pdf.cell(20, 10, 'Qtd (ml)', 1, 0, 'C', 1)
            pdf.cell(30, 10, 'Próxima Doação', 1, 1, 'C', 1)
            
            pdf.set_fill_color(255, 255, 255)
            
            # Obter dados das doações
            cursor = self.conn.cursor()
            if blood_type == 'Todos':
                cursor.execute('''
                    SELECT id, donor_name, donor_cpf, donor_blood_type, donation_date, quantity, next_donation_date
                    FROM donations
                    ORDER BY donation_date DESC
                ''')
            else:
                cursor.execute('''
                    SELECT id, donor_name, donor_cpf, donor_blood_type, donation_date, quantity, next_donation_date
                    FROM donations
                    WHERE donor_blood_type = ?
                    ORDER BY donation_date DESC
                ''', (blood_type,))
            
            today = datetime.now().date()
            
            for row in cursor.fetchall():
                donation_date = datetime.strptime(row[4], '%Y-%m-%d').date()
                next_donation = datetime.strptime(row[6], '%Y-%m-%d').date() if row[6] else None
                
                pdf.cell(15, 10, str(row[0]), 1, 0, 'C')
                pdf.cell(50, 10, row[1], 1, 0)
                pdf.cell(30, 10, row[2] or 'N/A', 1, 0)
                pdf.cell(20, 10, row[3], 1, 0, 'C')
                pdf.cell(30, 10, donation_date.strftime('%d/%m/%Y'), 1, 0, 'C')
                pdf.cell(20, 10, str(row[5]), 1, 0, 'C')
                
                if next_donation:
                    if next_donation <= today:
                        pdf.set_text_color(0, 128, 0)  # Verde
                        next_text = "PODE DOAR"
                    else:
                        pdf.set_text_color(0, 0, 0)  # Preto
                        next_text = next_donation.strftime('%d/%m/%Y')
                else:
                    next_text = "N/A"
                
                pdf.cell(30, 10, next_text, 1, 1, 'C')
                pdf.set_text_color(0, 0, 0)
            
            # Estatísticas
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Estatísticas', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Total de doações
            if blood_type == 'Todos':
                cursor.execute("SELECT COUNT(*), SUM(quantity) FROM donations")
            else:
                cursor.execute("SELECT COUNT(*), SUM(quantity) FROM donations WHERE donor_blood_type = ?", (blood_type,))
            
            total_count, total_ml = cursor.fetchone()
            total_ml = total_ml or 0
            
            pdf.cell(0, 10, f'Total de Doações: {total_count}', 0, 1)
            pdf.cell(0, 10, f'Volume Total Coletado: {total_ml} ml', 0, 1)
            
            # Doações por tipo (se não estiver filtrado)
            if blood_type == 'Todos':
                pdf.ln(5)
                pdf.cell(0, 10, 'Doações por Tipo Sanguíneo:', 0, 1)
                
                cursor.execute('''
                    SELECT donor_blood_type, COUNT(*), SUM(quantity)
                    FROM donations
                    GROUP BY donor_blood_type
                    ORDER BY COUNT(*) DESC
                ''')
                
                pdf.set_fill_color(200, 220, 255)
                pdf.cell(40, 10, 'Tipo Sanguíneo', 1, 0, 'C', 1)
                pdf.cell(30, 10, 'Doações', 1, 0, 'C', 1)
                pdf.cell(40, 10, 'Volume Total (ml)', 1, 1, 'C', 1)
                
                pdf.set_fill_color(255, 255, 255)
                
                for row in cursor.fetchall():
                    pdf.cell(40, 10, row[0], 1, 0, 'C')
                    pdf.cell(30, 10, str(row[1]), 1, 0, 'C')
                    pdf.cell(40, 10, str(row[2]), 1, 1, 'C')
            
            # Salvar PDF
            filename = f"relatorio_doacoes_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            pdf.output(filename)
            
            messagebox.showinfo("Sucesso", f"Relatório gerado com sucesso:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
            self.log_activity(f"Erro ao gerar relatório de doações: {str(e)}", level='ERROR')
    
    def create_admin_tab(self):
        """Cria a aba de administração"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="⚙️ Administração")
        
        # Notebook para sub-abas
        admin_notebook = ttk.Notebook(tab)
        admin_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sub-aba de usuários
        user_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(user_tab, text="👥 Usuários")
        self.create_user_management_tab(user_tab)
        
        # Sub-aba de tipos sanguíneos
        blood_types_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(blood_types_tab, text="🩸 Tipos Sanguíneos")
        self.create_blood_types_tab(blood_types_tab)
        
        # Sub-aba de configurações
        config_tab = ttk.Frame(admin_notebook)
        admin_notebook.add(config_tab, text="⚙️ Configurações")
        self.create_config_tab(config_tab)
    
    def create_user_management_tab(self, tab):
        """Cria a sub-aba de gerenciamento de usuários"""
        # Frame de usuários
        user_frame = ttk.LabelFrame(tab, text="Gerenciar Usuários", padding=10)
        user_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview de usuários
        self.users_tree = ttk.Treeview(user_frame, columns=('id', 'name', 'username', 'role', 'email', 'status'), show='headings')
        self.users_tree.heading('id', text='ID')
        self.users_tree.heading('name', text='Nome')
        self.users_tree.heading('username', text='Usuário')
        self.users_tree.heading('role', text='Perfil')
        self.users_tree.heading('email', text='E-mail')
        self.users_tree.heading('status', text='Status')
        
        self.users_tree.column('id', width=50, anchor='center')
        self.users_tree.column('name', width=150)
        self.users_tree.column('username', width=100)
        self.users_tree.column('role', width=80, anchor='center')
        self.users_tree.column('email', width=150)
        self.users_tree.column('status', width=80, anchor='center')
        
        self.users_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botões de controle
        btn_frame = ttk.Frame(user_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Adicionar", style='Primary.TButton',
                  command=self.show_add_user_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", style='Primary.TButton',
                  command=self.show_edit_user_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Ativar/Desativar", style='Secondary.TButton',
                  command=self.toggle_user_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Redefinir Senha", style='Success.TButton',
                  command=self.reset_user_password).pack(side=tk.LEFT, padx=5)
        
        # Atualizar lista de usuários
        self.update_users_list()
    
    def update_users_list(self):
        """Atualiza a lista de usuários"""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, username, role, email, is_active FROM users ORDER BY name")
        
        for row in cursor.fetchall():
            status = "Ativo" if row[5] else "Inativo"
            tags = () if row[5] else ('inactive',)
            self.users_tree.insert('', 'end', values=row[:5] + (status,), tags=tags)
        
        self.users_tree.tag_configure('inactive', foreground='gray')
    
    def show_add_user_dialog(self):
        """Mostra diálogo para adicionar novo usuário"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adicionar Usuário")
        dialog.geometry("400x350")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Nome:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        name_entry = ttk.Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Usuário:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        username_entry = ttk.Entry(dialog)
        username_entry.grid(row=1, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Senha:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        password_entry = ttk.Entry(dialog, show="•")
        password_entry.grid(row=2, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Confirmar Senha:").grid(row=3, column=0, padx=10, pady=10, sticky='e')
        confirm_entry = ttk.Entry(dialog, show="•")
        confirm_entry.grid(row=3, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Perfil:").grid(row=4, column=0, padx=10, pady=10, sticky='e')
        role_combo = ttk.Combobox(dialog, values=["admin", "doctor", "technician"], state="readonly")
        role_combo.current(0)
        role_combo.grid(row=4, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="E-mail:").grid(row=5, column=0, padx=10, pady=10, sticky='e')
        email_entry = ttk.Entry(dialog)
        email_entry.grid(row=5, column=1, padx=10, pady=10, sticky='we')
        
        def save_user():
            name = name_entry.get()
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()
            role = role_combo.get()
            email = email_entry.get()
            
            if not all([name, username, password, role]):
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return
            
            if password != confirm:
                messagebox.showerror("Erro", "As senhas não coincidem!")
                return
            
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, username, password, role, email) VALUES (?, ?, ?, ?, ?)",
                    (name, username, self.hash_password(password), role, email)
                    )
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Usuário adicionado com sucesso!")
                self.update_users_list()
                dialog.destroy()
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Nome de usuário já existe!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao adicionar usuário: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_edit_user_dialog(self):
        """Mostra diálogo para editar usuário existente"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário para editar!")
            return
        
        user_id = self.users_tree.item(selected[0])['values'][0]
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, username, role, email FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            messagebox.showerror("Erro", "Usuário não encontrado!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Usuário")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Nome:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        name_entry = ttk.Entry(dialog)
        name_entry.insert(0, user_data[0])
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Usuário:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        username_entry = ttk.Entry(dialog)
        username_entry.insert(0, user_data[1])
        username_entry.grid(row=1, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="Perfil:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        role_combo = ttk.Combobox(dialog, values=["admin", "doctor", "technician"], state="readonly")
        role_combo.set(user_data[2])
        role_combo.grid(row=2, column=1, padx=10, pady=10, sticky='we')
        
        ttk.Label(dialog, text="E-mail:").grid(row=3, column=0, padx=10, pady=10, sticky='e')
        email_entry = ttk.Entry(dialog)
        email_entry.insert(0, user_data[3] or "")
        email_entry.grid(row=3, column=1, padx=10, pady=10, sticky='we')
        
        def save_changes():
            name = name_entry.get()
            username = username_entry.get()
            role = role_combo.get()
            email = email_entry.get()
            
            if not all([name, username, role]):
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
                return
            
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE users SET name = ?, username = ?, role = ?, email = ? WHERE id = ?",
                    (name, username, role, email or None, user_id))
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso!")
                self.update_users_list()
                dialog.destroy()
                
                # Se o usuário editado for o atual, atualizar o nome na barra superior
                if user_id == self.current_user['id']:
                    self.current_user['name'] = name
                    self.current_user['role'] = role
                    self.show_main_interface()  # Recarregar a interface
                
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Nome de usuário já existe!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao atualizar usuário: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def toggle_user_status(self):
        """Ativa/desativa o usuário selecionado"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário para ativar/desativar!")
            return
        
        user_id = self.users_tree.item(selected[0])['values'][0]
        current_status = self.users_tree.item(selected[0])['values'][5] == "Ativo"
        
        if user_id == self.current_user['id']:
            messagebox.showerror("Erro", "Você não pode desativar sua própria conta!")
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE id = ?",
                (0 if current_status else 1, user_id))
            self.conn.commit()
            
            messagebox.showinfo("Sucesso", f"Usuário {'desativado' if current_status else 'ativado'} com sucesso!")
            self.update_users_list()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar status do usuário: {str(e)}")
    
    def reset_user_password(self):
        """Redefine a senha do usuário selecionado"""
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um usuário para redefinir a senha!")
            return
        
        user_id = self.users_tree.item(selected[0])['values'][0]
        username = self.users_tree.item(selected[0])['values'][2]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Redefinir Senha")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text=f"Redefinir senha para {username}").pack(pady=10)
        
        ttk.Label(dialog, text="Nova Senha:").pack()
        password_entry = ttk.Entry(dialog, show="•")
        password_entry.pack()
        
        ttk.Label(dialog, text="Confirmar Senha:").pack()
        confirm_entry = ttk.Entry(dialog, show="•")
        confirm_entry.pack()
        
        def save_password():
            password = password_entry.get()
            confirm = confirm_entry.get()
            
            if not password:
                messagebox.showerror("Erro", "Digite a nova senha!")
                return
            
            if password != confirm:
                messagebox.showerror("Erro", "As senhas não coincidem!")
                return
            
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (self.hash_password(password), user_id))
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Senha redefinida com sucesso!")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao redefinir senha: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_password).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_blood_types_tab(self, tab):
        """Cria a sub-aba de gerenciamento de tipos sanguíneos"""
        # Frame de tipos sanguíneos
        types_frame = ttk.LabelFrame(tab, text="Tipos Sanguíneos", padding=10)
        types_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview de tipos
        self.blood_types_tree = ttk.Treeview(types_frame, columns=('type', 'min_stock', 'description'), show='headings')
        self.blood_types_tree.heading('type', text='Tipo')
        self.blood_types_tree.heading('min_stock', text='Estoque Mínimo')
        self.blood_types_tree.heading('description', text='Descrição')
        
        self.blood_types_tree.column('type', width=80, anchor='center')
        self.blood_types_tree.column('min_stock', width=100, anchor='center')
        self.blood_types_tree.column('description', width=200)
        
        self.blood_types_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botões de controle
        btn_frame = ttk.Frame(types_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Editar", style='Primary.TButton',
                  command=self.edit_blood_type).pack(side=tk.LEFT, padx=5)
        
        # Atualizar lista de tipos
        self.update_blood_types_list()
    
    def update_blood_types_list(self):
        """Atualiza a lista de tipos sanguíneos"""
        for item in self.blood_types_tree.get_children():
            self.blood_types_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT type, min_stock, description FROM blood_types ORDER BY type")
        
        for row in cursor.fetchall():
            self.blood_types_tree.insert('', 'end', values=row)
    
    def edit_blood_type(self):
        """Edita o tipo sanguíneo selecionado"""
        selected = self.blood_types_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um tipo sanguíneo para editar!")
            return
        
        blood_type = self.blood_types_tree.item(selected[0])['values'][0]
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT min_stock, description FROM blood_types WHERE type = ?", (blood_type,))
        type_data = cursor.fetchone()
        
        if not type_data:
            messagebox.showerror("Erro", "Tipo sanguíneo não encontrado!")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Editar {blood_type}")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text=f"Tipo Sanguíneo: {blood_type}", font=('Arial', 11, 'bold')).pack(pady=10)
        
        ttk.Label(dialog, text="Estoque Mínimo:").pack()
        min_stock_entry = ttk.Entry(dialog)
        min_stock_entry.insert(0, type_data[0])
        min_stock_entry.pack()
        
        ttk.Label(dialog, text="Descrição:").pack()
        desc_entry = ttk.Entry(dialog)
        desc_entry.insert(0, type_data[1] or "")
        desc_entry.pack()
        
        def save_changes():
            min_stock = min_stock_entry.get()
            description = desc_entry.get()
            
            if not min_stock:
                messagebox.showerror("Erro", "Informe o estoque mínimo!")
                return
            
            try:
                min_stock = int(min_stock)
                if min_stock < 0:
                    raise ValueError
                
                cursor.execute(
                    "UPDATE blood_types SET min_stock = ?, description = ? WHERE type = ?",
                    (min_stock, description or None, blood_type))
                self.conn.commit()
                
                messagebox.showinfo("Sucesso", "Tipo sanguíneo atualizado com sucesso!")
                self.update_blood_types_list()
                self.update_stock_display()  # Atualizar status no estoque
                dialog.destroy()
                
                # Verificar se estoque está abaixo do novo mínimo
                self.check_stock_levels(blood_type)
                
            except ValueError:
                messagebox.showerror("Erro", "Estoque mínimo deve ser um número positivo!")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao atualizar tipo sanguíneo: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Salvar", style='Primary.TButton', command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_config_tab(self, tab):
        """Cria a sub-aba de configurações do sistema"""
        # Frame de configurações
        config_frame = ttk.LabelFrame(tab, text="Configurações do Sistema", padding=15)
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configurações de e-mail
        ttk.Label(config_frame, text="Configurações de E-mail:", font=('Arial', 11, 'bold')).pack(anchor='w', pady=(0, 10))
        
        ttk.Label(config_frame, text="Servidor SMTP:").pack(anchor='w')
        smtp_entry = ttk.Entry(config_frame)
        smtp_entry.insert(0, self.email_config['smtp_server'])
        smtp_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(config_frame, text="Porta:").pack(anchor='w')
        port_entry = ttk.Entry(config_frame)
        port_entry.insert(0, str(self.email_config['smtp_port']))
        port_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(config_frame, text="E-mail do Sistema:").pack(anchor='w')
        email_entry = ttk.Entry(config_frame)
        email_entry.insert(0, self.email_config['email'])
        email_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(config_frame, text="Senha:").pack(anchor='w')
        pass_entry = ttk.Entry(config_frame, show="•")
        pass_entry.insert(0, self.email_config['password'])
        pass_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Botão para testar e-mail
        ttk.Button(config_frame, text="Testar Conexão SMTP", style='Primary.TButton',
                  command=lambda: self.test_smtp_connection(
                      smtp_entry.get(),
                      port_entry.get(),
                      email_entry.get(),
                      pass_entry.get()
                  )).pack(pady=5)
        
        # Botão para salvar configurações
        ttk.Button(config_frame, text="Salvar Configurações", style='Success.TButton',
                  command=lambda: self.save_email_config(
                      smtp_entry.get(),
                      port_entry.get(),
                      email_entry.get(),
                      pass_entry.get()
                  )).pack(pady=5)
        
        # Frame de backup
        backup_frame = ttk.LabelFrame(tab, text="Backup do Sistema", padding=15)
        backup_frame.pack(fill=tk.BOTH, padx=10, pady=10)
        
        ttk.Button(backup_frame, text="Fazer Backup Agora", style='Primary.TButton',
                  command=self.create_backup).pack(pady=5)
        
        ttk.Button(backup_frame, text="Restaurar Backup", style='Secondary.TButton',
                  command=self.restore_backup).pack(pady=5)
    
    def test_smtp_connection(self, server, port, email, password):
        """Testa a conexão com o servidor SMTP"""
        if not all([server, port, email, password]):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        try:
            port = int(port)
            with smtplib.SMTP(server, port) as smtp:
                smtp.starttls()
                smtp.login(email, password)
            
            messagebox.showinfo("Sucesso", "Conexão SMTP bem-sucedida!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na conexão SMTP: {str(e)}")
    
    def save_email_config(self, server, port, email, password):
        """Salva as configurações de e-mail"""
        if not all([server, port, email, password]):
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        
        try:
            port = int(port)
            self.email_config = {
                'smtp_server': server,
                'smtp_port': port,
                'email': email,
                'password': password
            }
            
            # Em um sistema real, você salvaria isso em um arquivo de configuração
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
        except ValueError:
            messagebox.showerror("Erro", "Porta deve ser um número!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar configurações: {str(e)}")
    
    def create_backup(self):
        """Cria um backup do banco de dados"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"blood_bank_backup_{timestamp}.db")
            
            # Fechar a conexão atual para permitir a cópia
            self.conn.close()
            
            # Copiar o arquivo do banco de dados
            import shutil
            shutil.copy2(DB_NAME, backup_file)
            
            # Reconectar
            self.conn = sqlite3.connect(DB_NAME)
            
            messagebox.showinfo("Sucesso", f"Backup criado com sucesso:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar backup: {str(e)}")
            # Tentar reconectar mesmo em caso de erro
            self.conn = sqlite3.connect(DB_NAME)
    
    def restore_backup(self):
        """Restaura um backup do banco de dados"""
        try:
            from tkinter import filedialog
            backup_file = filedialog.askopenfilename(
                title="Selecione o arquivo de backup",
                filetypes=[("Banco de dados SQLite", "*.db"), ("Todos os arquivos", "*.*")]
            )
            
            if not backup_file:
                return
            
            # Confirmar restauração
            if not messagebox.askyesno("Confirmar", "Tem certeza que deseja restaurar este backup? Todos os dados atuais serão substituídos."):
                return
            
            # Fechar a conexão atual
            self.conn.close()
            
            # Substituir o banco de dados atual pelo backup
            import shutil
            shutil.copy2(backup_file, DB_NAME)
            
            # Reconectar
            self.conn = sqlite3.connect(DB_NAME)
            
            messagebox.showinfo("Sucesso", "Backup restaurado com sucesso! Reinicie o sistema para aplicar as alterações.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao restaurar backup: {str(e)}")
            # Tentar reconectar mesmo em caso de erro
            self.conn = sqlite3.connect(DB_NAME)
    
    def create_analytics_tab(self):
        """Cria a aba de análise preditiva (admin)"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🔮 Análise Preditiva")
        
        # Frame de controle
        control_frame = ttk.Frame(tab, padding=10)
        control_frame.pack(fill=tk.X)
        
        ttk.Label(control_frame, text="Tipo Sanguíneo:").grid(row=0, column=0, padx=5)
        self.analytics_type_combo = ttk.Combobox(control_frame, state="readonly")
        self.analytics_type_combo.grid(row=0, column=1, padx=5)
        self.update_blood_types_analytics()
        
        ttk.Label(control_frame, text="Dias para prever:").grid(row=0, column=2, padx=5)
        self.forecast_days_combo = ttk.Combobox(control_frame, values=[7, 14, 30], state="readonly")
        self.forecast_days_combo.current(0)
        self.forecast_days_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(control_frame, text="Gerar Previsão", style='Primary.TButton',
                  command=self.generate_forecast).grid(row=0, column=4, padx=5)
        
        ttk.Button(control_frame, text="Gerar Relatório", style='Success.TButton',
                  command=self.generate_analytics_report).grid(row=0, column=5, padx=5)
        
        # Notebook para diferentes análises
        analytics_notebook = ttk.Notebook(tab)
        analytics_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de previsão de demanda
        forecast_tab = ttk.Frame(analytics_notebook)
        analytics_notebook.add(forecast_tab, text="Previsão de Demanda")
        
        self.forecast_fig = plt.Figure(figsize=(10, 5), dpi=100)
        self.forecast_ax = self.forecast_fig.add_subplot(111)
        self.forecast_canvas = FigureCanvasTkAgg(self.forecast_fig, forecast_tab)
        self.forecast_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Aba de estoque vs demanda
        stock_vs_demand_tab = ttk.Frame(analytics_notebook)
        analytics_notebook.add(stock_vs_demand_tab, text="Estoque vs Demanda")
        
        self.stock_demand_fig = plt.Figure(figsize=(10, 5), dpi=100)
        self.stock_demand_ax = self.stock_demand_fig.add_subplot(111)
        self.stock_demand_canvas = FigureCanvasTkAgg(self.stock_demand_fig, stock_vs_demand_tab)
        self.stock_demand_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Frame de recomendações
        self.recommendation_frame = ttk.Frame(tab)
        self.recommendation_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(self.recommendation_frame, text="Recomendações:", font=('Arial', 12, 'bold')).pack(anchor='w')
        self.recommendation_text = tk.Text(self.recommendation_frame, height=6, wrap=tk.WORD)
        self.recommendation_text.pack(fill=tk.X, pady=5)
        
        # Gerar gráfico inicial de estoque vs demanda
        self.generate_stock_vs_demand_chart()
    
    def update_blood_types_analytics(self):
        """Atualiza a lista de tipos sanguíneos para análise"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT type FROM blood_types ORDER BY type")
        types = [row[0] for row in cursor.fetchall()]
        self.analytics_type_combo['values'] = types
        if types:
            self.analytics_type_combo.current(0)
    
    def generate_forecast(self):
        """Gera previsão de demanda usando machine learning"""
        blood_type = self.analytics_type_combo.get()
        days_to_predict = int(self.forecast_days_combo.get())
        
        if not blood_type:
            messagebox.showerror("Erro", "Selecione um tipo sanguíneo!")
            return
        
        try:
            # Obter dados históricos
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT date(request_date) as day, SUM(quantity) as daily_usage
                FROM requests
                WHERE blood_type = ? AND status = 'approved'
                GROUP BY day
                ORDER BY day
            ''', (blood_type,))
            
            data = cursor.fetchall()
            
            if len(data) < 30:
                messagebox.showwarning("Aviso", 
                    f"Dados insuficientes para {blood_type}. Necessário pelo menos 30 dias de histórico.")
                return
            
            # Preparar dados para o modelo
            dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
            usages = [row[1] for row in data]
            
            # Criar features (dias desde a primeira data)
            day_numbers = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
            
            # Treinar modelo Random Forest
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(day_numbers, usages)
            
            # Prever para os próximos dias
            last_day = day_numbers[-1][0]
            future_days = np.array([last_day + i for i in range(1, days_to_predict + 1)]).reshape(-1, 1)
            predictions = model.predict(future_days)
            
            # Gerar datas futuras
            future_dates = [dates[-1] + timedelta(days=i) for i in range(1, days_to_predict + 1)]
            
            # Plotar resultados
            self.forecast_ax.clear()
            
            # Histórico
            self.forecast_ax.plot(dates, usages, label='Histórico', marker='o')
            
            # Previsão
            self.forecast_ax.plot(future_dates, predictions, label='Previsão', linestyle='--', marker='o', color='red')
            
            self.forecast_ax.set_title(f'Previsão de Demanda para {blood_type}')
            self.forecast_ax.set_xlabel('Data')
            self.forecast_ax.set_ylabel('Unidades')
            self.forecast_ax.legend()
            self.forecast_ax.grid(True)
            self.forecast_fig.autofmt_xdate()
            
            self.forecast_canvas.draw()
            
            # Gerar recomendações
            self.generate_recommendations(blood_type, predictions, future_dates)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar previsão: {str(e)}")
            self.log_activity(f"Erro na previsão: {str(e)}", level='ERROR')
    
    def generate_stock_vs_demand_chart(self):
        """Gera gráfico comparando estoque atual com demanda média"""
        try:
            cursor = self.conn.cursor()
            
            # Obter estoque atual por tipo
            cursor.execute('''
                SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock
                FROM blood_types b
                LEFT JOIN stock s ON b.type = s.blood_type
                GROUP BY b.type
                ORDER BY b.type
            ''')
            
            stock_data = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
            
            # Obter demanda média por tipo (últimos 30 dias)
            cursor.execute('''
                SELECT blood_type, AVG(daily_usage)
                FROM (
                    SELECT blood_type, date(request_date) as day, SUM(quantity) as daily_usage
                    FROM requests
                    WHERE status = 'approved' AND date(request_date) >= date('now', '-30 days')
                    GROUP BY blood_type, day
                )
                GROUP BY blood_type
            ''')
            
            demand_data = {row[0]: row[1] for row in cursor.fetchall() if row[1] is not None}
            
            # Preparar dados para o gráfico
            types = sorted(stock_data.keys())
            stock = [stock_data[t][0] for t in types]
            min_stock = [stock_data[t][1] for t in types]
            demand = [demand_data.get(t, 0) for t in types]
            
            # Plotar gráfico
            self.stock_demand_ax.clear()
            
            x = np.arange(len(types))
            width = 0.25
            
            self.stock_demand_ax.bar(x - width, stock, width, label='Estoque Atual', color='#d90429')
            self.stock_demand_ax.bar(x, min_stock, width, label='Estoque Mínimo', color='#ef233c')
            self.stock_demand_ax.bar(x + width, demand, width, label='Demanda Média (30 dias)', color='#2b2d42')
            
            self.stock_demand_ax.set_title('Estoque vs Demanda por Tipo Sanguíneo')
            self.stock_demand_ax.set_xlabel('Tipo Sanguíneo')
            self.stock_demand_ax.set_ylabel('Unidades')
            self.stock_demand_ax.set_xticks(x)
            self.stock_demand_ax.set_xticklabels(types)
            self.stock_demand_ax.legend()
            self.stock_demand_ax.grid(True, linestyle='--', alpha=0.6)
            
            self.stock_demand_canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar gráfico: {str(e)}")
            self.log_activity(f"Erro no gráfico estoque vs demanda: {str(e)}", level='ERROR')
    
    def generate_recommendations(self, blood_type, predictions, future_dates):
        """Gera recomendações baseadas na previsão"""
        cursor = self.conn.cursor()
        
        # Obter estoque atual
        cursor.execute('''
            SELECT SUM(quantity) FROM stock WHERE blood_type = ?
        ''', (blood_type,))
        current_stock = cursor.fetchone()[0] or 0
        
        # Obter estoque mínimo
        cursor.execute('''
            SELECT min_stock FROM blood_types WHERE type = ?
        ''', (blood_type,))
        min_stock = cursor.fetchone()[0]
        
        # Calcular demanda total prevista
        total_predicted = sum(predictions)
        avg_daily = total_predicted / len(predictions)
        
        # Identificar pico de demanda
        peak_day_idx = np.argmax(predictions)
        peak_date = future_dates[peak_day_idx]
        peak_demand = predictions[peak_day_idx]
        
        # Gerar texto de recomendações
        recommendations = f"Recomendações para {blood_type}:\n\n"
        recommendations += f"- Estoque atual: {current_stock} unidades\n"
        recommendations += f"- Estoque mínimo recomendado: {min_stock} unidades\n"
        recommendations += f"- Demanda prevista para os próximos {len(predictions)} dias: {total_predicted:.1f} unidades\n"
        recommendations += f"- Demanda média diária prevista: {avg_daily:.1f} unidades/dia\n"
        recommendations += f"- Pico de demanda previsto: {peak_demand:.1f} unidades em {peak_date.strftime('%d/%m/%Y')}\n\n"
        
        if current_stock >= total_predicted + min_stock:
            recommendations += "✅ Estoque suficiente para atender à demanda prevista e manter o mínimo recomendado."
        else:
            deficit = (total_predicted + min_stock) - current_stock
            recommendations += f"⚠️ Atenção: Déficit previsto de {deficit:.1f} unidades.\n"
            recommendations += f"- Recomendação: Obter pelo menos {max(deficit, min_stock)} unidades adicionais.\n"
            
            # Sugerir prioridade baseada no pico de demanda
            days_until_peak = (peak_date - datetime.now().date()).days
            if days_until_peak < 7:
                recommendations += f"- Prioridade ALTA: Pico de demanda em {days_until_peak} dias.\n"
            elif days_until_peak < 14:
                recommendations += f"- Prioridade MÉDIA: Pico de demanda em {days_until_peak} dias.\n"
            else:
                recommendations += f"- Prioridade BAIXA: Pico de demanda em {days_until_peak} dias.\n"
            
            # Verificar se há doadores frequentes deste tipo
            cursor.execute('''
                SELECT COUNT(*) 
                FROM donations 
                WHERE donor_blood_type = ? AND date(next_donation_date) <= date('now')
            ''', (blood_type,))
            eligible_donors = cursor.fetchone()[0]
            
            if eligible_donors > 0:
                recommendations += f"- {eligible_donors} doadores deste tipo podem doar novamente. Considere contatá-los.\n"
        
        self.recommendation_text.delete(1.0, tk.END)
        self.recommendation_text.insert(tk.END, recommendations)
    
    def generate_analytics_report(self):
        """Gera relatório PDF completo de análises"""
        try:
            blood_type = self.analytics_type_combo.get()
            if not blood_type:
                messagebox.showerror("Erro", "Selecione um tipo sanguíneo para gerar o relatório!")
                return
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            pdf.cell(0, 10, 'Relatório de Análise Preditiva', 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Tipo Sanguíneo: {blood_type}', 0, 1, 'C')
            pdf.cell(0, 10, f'Emitido em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            pdf.cell(0, 10, f'Emitido por: {self.current_user["name"]}', 0, 1, 'C')
            pdf.ln(10)
            
            # Seção 1: Estoque Atual
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '1. Situação Atual do Estoque', 0, 1)
            pdf.set_font('Arial', '', 12)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT SUM(quantity) FROM stock WHERE blood_type = ?
            ''', (blood_type,))
            current_stock = cursor.fetchone()[0] or 0
            
            cursor.execute('''
                SELECT min_stock FROM blood_types WHERE type = ?
            ''', (blood_type,))
            min_stock = cursor.fetchone()[0]
            
            pdf.cell(0, 10, f'- Estoque atual: {current_stock} unidades', 0, 1)
            pdf.cell(0, 10, f'- Estoque mínimo recomendado: {min_stock} unidades', 0, 1)
            
            status = "✅ Suficiente" if current_stock >= min_stock else "⚠️ Abaixo do mínimo"
            pdf.cell(0, 10, f'- Status: {status}', 0, 1)
            pdf.ln(5)
            
            # Seção 2: Análise de Demanda
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '2. Análise de Demanda', 0, 1)
            pdf.set_font('Arial', '', 12)
            
            # Demanda dos últimos 30 dias
            cursor.execute('''
                SELECT AVG(daily_usage), MAX(daily_usage), MIN(daily_usage)
                FROM (
                    SELECT date(request_date) as day, SUM(quantity) as daily_usage
                    FROM requests
                    WHERE blood_type = ? AND status = 'approved' AND date(request_date) >= date('now', '-30 days')
                    GROUP BY day
                )
            ''', (blood_type,))
            
            avg_demand, max_demand, min_demand = cursor.fetchone()
            
            if avg_demand:
                pdf.cell(0, 10, f'- Demanda média (últimos 30 dias): {avg_demand:.1f} unidades/dia', 0, 1)
                pdf.cell(0, 10, f'- Máxima diária: {max_demand:.1f} unidades', 0, 1)
                pdf.cell(0, 10, f'- Mínima diária: {min_demand:.1f} unidades', 0, 1)
            else:
                pdf.cell(0, 10, '- Sem dados de demanda nos últimos 30 dias', 0, 1)
            
            pdf.ln(5)
            
            # Seção 3: Previsão
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '3. Previsão de Demanda', 0, 1)
            pdf.set_font('Arial', '', 12)
            
            days_to_predict = int(self.forecast_days_combo.get())
            
            # Obter dados históricos para previsão
            cursor.execute('''
                SELECT date(request_date) as day, SUM(quantity) as daily_usage
                FROM requests
                WHERE blood_type = ? AND status = 'approved'
                GROUP BY day
                ORDER BY day
            ''', (blood_type,))
            
            data = cursor.fetchall()
            
            if len(data) >= 30:
                dates = [datetime.strptime(row[0], '%Y-%m-%d') for row in data]
                usages = [row[1] for row in data]
                
                # Treinar modelo
                day_numbers = np.array([(d - dates[0]).days for d in dates]).reshape(-1, 1)
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(day_numbers, usages)
                
                # Fazer previsão
                last_day = day_numbers[-1][0]
                future_days = np.array([last_day + i for i in range(1, days_to_predict + 1)]).reshape(-1, 1)
                predictions = model.predict(future_days)
                
                total_predicted = sum(predictions)
                avg_daily_predicted = total_predicted / days_to_predict
                peak_day_idx = np.argmax(predictions)
                peak_demand = predictions[peak_day_idx]
                
                pdf.cell(0, 10, f'- Período de previsão: {days_to_predict} dias', 0, 1)
                pdf.cell(0, 10, f'- Demanda total prevista: {total_predicted:.1f} unidades', 0, 1)
                pdf.cell(0, 10, f'- Demanda média prevista: {avg_daily_predicted:.1f} unidades/dia', 0, 1)
                pdf.cell(0, 10, f'- Pico de demanda previsto: {peak_demand:.1f} unidades', 0, 1)
                
                # Adicionar gráfico de previsão
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, 'Gráfico de Previsão de Demanda', 0, 1)
                
                # Criar gráfico temporário para salvar como imagem
                fig = plt.Figure(figsize=(8, 4), dpi=100)
                ax = fig.add_subplot(111)
                
                future_dates = [dates[-1] + timedelta(days=i) for i in range(1, days_to_predict + 1)]
                
                ax.plot(dates, usages, label='Histórico', marker='o')
                ax.plot(future_dates, predictions, label='Previsão', linestyle='--', marker='o', color='red')
                
                ax.set_title(f'Previsão de Demanda para {blood_type}')
                ax.set_xlabel('Data')
                ax.set_ylabel('Unidades')
                ax.legend()
                ax.grid(True)
                fig.autofmt_xdate()
                
                # Salvar gráfico como imagem temporária
                temp_img = "temp_forecast.png"
                fig.savefig(temp_img, bbox_inches='tight')
                plt.close(fig)
                
                # Adicionar imagem ao PDF
                pdf.image(temp_img, x=10, w=190)
                os.remove(temp_img)  # Remover arquivo temporário
            else:
                pdf.cell(0, 10, '- Dados insuficientes para previsão (mínimo 30 dias de histórico)', 0, 1)
            
            pdf.ln(10)
            
            # Seção 4: Recomendações
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, '4. Recomendações', 0, 1)
            pdf.set_font('Arial', '', 12)
            
            if len(data) >= 30:
                required_stock = total_predicted + min_stock
                deficit = required_stock - current_stock
                
                if current_stock >= required_stock:
                    pdf.cell(0, 10, '- Estoque suficiente para atender à demanda prevista e manter o mínimo recomendado.', 0, 1)
                else:
                    pdf.cell(0, 10, f'- Estoque insuficiente. Déficit previsto: {deficit:.1f} unidades', 0, 1)
                    pdf.cell(0, 10, f'- Recomendação: Obter pelo menos {max(deficit, min_stock)} unidades adicionais', 0, 1)
                    
                    # Verificar doadores elegíveis
                    cursor.execute('''
                        SELECT COUNT(*) 
                        FROM donations 
                        WHERE donor_blood_type = ? AND date(next_donation_date) <= date('now')
                    ''', (blood_type,))
                    eligible_donors = cursor.fetchone()[0]
                    
                    if eligible_donors > 0:
                        pdf.cell(0, 10, f'- {eligible_donors} doadores deste tipo podem doar novamente. Considere contatá-los.', 0, 1)
            else:
                pdf.cell(0, 10, '- Coletar mais dados históricos para gerar recomendações precisas.', 0, 1)
            
            # Salvar PDF
            filename = f"relatorio_analise_{blood_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            pdf.output(filename)
            
            messagebox.showinfo("Sucesso", f"Relatório gerado com sucesso:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório: {str(e)}")
            self.log_activity(f"Erro ao gerar relatório de análise: {str(e)}", level='ERROR')
    
    def create_chatbot_tab(self):
        """Cria a aba do chatbot de suporte"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="💬 Hemolife Assistant")
        
        # Frame do chat
        chat_frame = ttk.Frame(tab)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Área de mensagens
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state='disabled')
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Frame de entrada
        input_frame = ttk.Frame(tab)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.user_input = ttk.Entry(input_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.user_input.bind('<Return>', lambda e: self.send_chat_message())
        
        send_btn = ttk.Button(input_frame, text="Enviar", style='Primary.TButton',
                            command=self.send_chat_message)
        send_btn.pack(side=tk.RIGHT)
        
        # Mensagem de boas-vindas
        self.add_chat_message("assistant", "Olá! Sou o Hemolife Assistant. Como posso ajudar você hoje?")
        self.add_chat_message("assistant", "Você pode me perguntar sobre:\n- Níveis de estoque\n- Requisições pendentes\n- Estatísticas de doação\n- Previsões de demanda\n- Como usar o sistema")
    
    def add_chat_message(self, sender, message):
        """Adiciona uma mensagem ao chat"""
        self.chat_display.config(state='normal')
        
        if sender == "user":
            self.chat_display.insert(tk.END, "Você: ", 'user_tag')
            self.chat_display.insert(tk.END, f"{message}\n\n")
        else:
            self.chat_display.insert(tk.END, "Assistente: ", 'assistant_tag')
            self.chat_display.insert(tk.END, f"{message}\n\n")
        
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        
        # Configurar tags para cores
        self.chat_display.tag_config('user_tag', foreground='#d90429', font=('Arial', 10, 'bold'))
        self.chat_display.tag_config('assistant_tag', foreground='#2b2d42', font=('Arial', 10, 'bold'))
    
    def send_chat_message(self):
        """Processa a mensagem do usuário e gera resposta"""
        message = self.user_input.get().strip()
        if not message:
            return
        
        self.add_chat_message("user", message)
        self.user_input.delete(0, tk.END)
        
        # Processar a mensagem e gerar resposta
        response = self.generate_chat_response(message)
        self.add_chat_message("assistant", response)
    
    def generate_chat_response(self, message):
        """Gera uma resposta do chatbot baseada na mensagem do usuário"""
        message = message.lower()
        
        # Verificar estoque
        if "estoque" in message or "disponível" in message or "sangue" in message:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock 
                FROM blood_types b
                LEFT JOIN stock s ON b.type = s.blood_type
                GROUP BY b.type
                ORDER BY b.type
            ''')
            
            stock_data = cursor.fetchall()
            response = "Níveis de Estoque Atual:\n\n"
            
            for row in stock_data:
                status = "✅ OK" if row[1] >= row[2] else f"⚠️ Baixo (mín: {row[2]})"
                response += f"{row[0]}: {row[1]} unidades - {status}\n"
            
            return response
        
        # Requisições pendentes
        elif "pendente" in message or "requisição" in message or "solicitação" in message:
            if self.current_user['role'] not in ['admin', 'technician']:
                return "Apenas administradores e técnicos podem ver informações sobre requisições pendentes."
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM requests WHERE status = 'pending'
            ''')
            pending_count = cursor.fetchone()[0]
            
            return f"Existem {pending_count} requisições pendentes de aprovação no momento."
        
        # Estatísticas de doação
        elif "doação" in message or "doador" in message or "doar" in message:
            cursor = self.conn.cursor()
            
            # Total de doações
            cursor.execute("SELECT COUNT(*), SUM(quantity) FROM donations")
            total_count, total_ml = cursor.fetchone()
            total_ml = total_ml or 0
            
            # Doações recentes
            cursor.execute("SELECT COUNT(*) FROM donations WHERE date(donation_date) >= date('now', '-7 days')")
            recent_count = cursor.fetchone()[0]
            
            response = (
                f"Estatísticas de Doação:\n\n"
                f"- Total de doações registradas: {total_count}\n"
                f"- Volume total coletado: {total_ml} ml\n"
                f"- Doações nos últimos 7 dias: {recent_count}\n\n"
                f"Lembre-se: Cada doação pode salvar até 3 vidas!"
            )
            
            return response
        
        # Previsão de demanda
        elif "previsão" in message or "demanda" in message or "futuro" in message:
            if self.current_user['role'] != 'admin':
                return "Apenas administradores podem acessar informações de previsão de demanda."
            
            return "Para ver previsões detalhadas, acesse a aba 'Análise Preditiva' no menu."
        
        # Ajuda geral
        elif "ajuda" in message or "como usar" in message or "funciona" in message:
            response = (
                "O sistema Hemolife Pro possui várias funcionalidades:\n\n"
                "- 📦 Estoque: Verifique os níveis atuais de estoque\n"
                "- 📋 Requisições: Gerencie requisições de sangue (para técnicos/admins)\n"
                "- 🩺 Solicitar Sangue: Faça requisições de sangue (para médicos)\n"
                "- 🩹 Doações: Registre novas doações de sangue\n"
                "- 🔮 Análise Preditiva: Veja previsões de demanda (para admins)\n"
                "- ⚙️ Administração: Gerencie usuários e configurações (para admins)\n\n"
                "Digite sua dúvida específica para obter mais informações."
            )
            return response
        
        # Mensagem padrão
        else:
            return "Desculpe, não entendi sua pergunta. Você pode reformular ou perguntar sobre:\n- Estoque\n- Requisições\n- Doações\n- Previsões\n- Como usar o sistema"
    
    def generate_request_report(self):
        """Gera relatório PDF das requisições"""
        selected = self.requests_tree.selection()
        filter_status = self.filter_combo.get()
        
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Título
            title = 'Relatório de Requisições de Sangue'
            if filter_status != 'Todas':
                title += f' ({filter_status})'
            
            pdf.cell(0, 10, title, 0, 1, 'C')
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Emitido em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
            pdf.cell(0, 10, f'Emitido por: {self.current_user["name"]}', 0, 1, 'C')
            pdf.ln(10)
            
            if selected:
                # Relatório individual
                request_id = self.requests_tree.item(selected[0])['values'][0]
                
                cursor = self.conn.cursor()
                cursor.execute('''
                    SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status, 
                           r.urgency, r.patient_info, r.response_date, u2.name
                    FROM requests r
                    JOIN users u ON r.requesting_doctor = u.id
                    LEFT JOIN users u2 ON r.responding_staff = u2.id
                    WHERE r.id = ?
                ''', (request_id,))
                
                request_data = cursor.fetchone()
                
                if request_data:
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, f'Requisição #{request_id}', 0, 1)
                    pdf.set_font('Arial', '', 12)
                    
                    fields = [
                        ("Tipo Sanguíneo:", request_data[1]),
                        ("Quantidade:", str(request_data[2])),
                        ("Médico Solicitante:", request_data[3]),
                        ("Data da Requisição:", request_data[4]),
                        ("Status:", {
                            'pending': 'Pendente',
                            'approved': 'Aprovada',
                            'rejected': 'Rejeitada'
                        }.get(request_data[5], request_data[5])),
                        ("Urgência:", request_data[6] or "Normal"),
                        ("Informações do Paciente:", request_data[7] or "Não informado"),
                        ("Data da Resposta:", request_data[8] or "N/A"),
                        ("Responsável pela Resposta:", request_data[9] or "N/A")
                    ]
                    
                    for label, value in fields:
                        pdf.cell(50, 10, label, 0, 0)
                        pdf.cell(0, 10, value, 0, 1)
            else:
                # Relatório múltiplo
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(15, 10, 'ID', 1, 0, 'C', 1)
                pdf.cell(30, 10, 'Tipo', 1, 0, 'C', 1)
                pdf.cell(25, 10, 'Qtd', 1, 0, 'C', 1)
                pdf.cell(60, 10, 'Médico', 1, 0, 'C', 1)
                pdf.cell(40, 10, 'Data', 1, 0, 'C', 1)
                pdf.cell(20, 10, 'Status', 1, 1, 'C', 1)
                
                pdf.set_font('Arial', '', 10)
                
                cursor = self.conn.cursor()
                status_map = {"Todas": None, "Pendentes": "pending", "Aprovadas": "approved", "Rejeitadas": "rejected"}
                status = status_map[filter_status]
                
                if status:
                    cursor.execute('''
                        SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status
                        FROM requests r
                        JOIN users u ON r.requesting_doctor = u.id
                        WHERE r.status = ?
                        ORDER BY r.request_date DESC
                    ''', (status,))
                else:
                    cursor.execute('''
                        SELECT r.id, r.blood_type, r.quantity, u.name, r.request_date, r.status
                        FROM requests r
                        JOIN users u ON r.requesting_doctor = u.id
                        ORDER BY r.request_date DESC
                    ''')
                
                for row in cursor.fetchall():
                    pdf.cell(15, 10, str(row[0]), 1, 0, 'C')
                    pdf.cell(30, 10, row[1], 1, 0, 'C')
                    pdf.cell(25, 10, str(row[2]), 1, 0, 'C')
                    pdf.cell(60, 10, row[3], 1, 0)
                    pdf.cell(40, 10, row[4], 1, 0, 'C')
                    
                    status_text = {
                        'pending': 'Pendente',
                        'approved': 'Aprovada',
                        'rejected': 'Rejeitada'
                    }.get(row[5], row[5])
                    
                    # Cores para status
                    if status_text == 'Aprovada':
                        pdf.set_text_color(0, 128, 0)  # Verde
                    elif status_text == 'Rejeitada':
                        pdf.set_text_color(255, 0, 0)  # Vermelho
                    
                    pdf.cell(20, 10, status_text, 1, 1, 'C')
                    pdf.set_text_color(0, 0, 0)  # Volta ao preto
            
            # Salvar PDF
            if selected:
                filename = f"requisicao_{request_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
            else:
                filename = f"relatorio_requisicoes_{filter_status.lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            pdf.output(filename)
            messagebox.showinfo("Sucesso", f"Relatório gerado:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar relatório PDF: {str(e)}")
            self.log_activity(f"Erro ao gerar PDF: {str(e)}", level='ERROR')
    
    def show_alerts(self):
        """Mostra a janela de alertas/notificações"""
        if not self.alerts:
            messagebox.showinfo("Alertas", "Você não tem novas notificações.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Notificações")
        dialog.geometry("500x400")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista de alertas
        alert_list = tk.Listbox(main_frame, font=('Arial', 10))
        alert_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        for alert in self.alerts:
            alert_list.insert(tk.END, f"{alert['date']} - {alert['message']}")
        
        # Frame de botões
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def mark_as_read():
            selected = alert_list.curselection()
            if not selected:
                return
            
            alert_id = self.alerts[selected[0]]['id']
            
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE alerts SET status = 'read' WHERE id = ?",
                    (alert_id,))
                self.conn.commit()
                
                # Remover da lista local
                self.alerts.pop(selected[0])
                alert_list.delete(selected[0])
                
                # Atualizar contador na barra superior
                self.alert_btn.config(text=f"🔔 {len(self.alerts)}" if self.alerts else "🔔")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao marcar como lido: {str(e)}")
        
        ttk.Button(btn_frame, text="Marcar como Lido", style='Primary.TButton',
                  command=mark_as_read).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fechar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def check_low_stock(self):
        """Verifica e alerta sobre estoque baixo"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT b.type, COALESCE(SUM(s.quantity), 0), b.min_stock 
            FROM blood_types b
            LEFT JOIN stock s ON b.type = s.blood_type
            GROUP BY b.type
            HAVING SUM(s.quantity) < b.min_stock OR SUM(s.quantity) IS NULL
        ''')
        
        low_stock = cursor.fetchall()
        
        if low_stock:
            message = "Atenção! Estoque baixo para os seguintes tipos:\n\n"
            for row in low_stock:
                message += f"- {row[0]}: {row[1]} unidades (mínimo: {row[2]})\n"
            
            # Registrar alerta para administradores
            cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1")
            admins = cursor.fetchall()
            
            for admin_id, in admins:
                cursor.execute('''
                    INSERT INTO alerts (type, message, recipient_id, sent_date, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('low_stock', message, admin_id, datetime.now().isoformat(), 'sent'))
            
            self.conn.commit()
    
    def check_stock_levels(self, blood_type):
        """Verifica os níveis de estoque para um tipo específico"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(quantity), 0), min_stock 
            FROM stock
            JOIN blood_types ON stock.blood_type = blood_types.type
            WHERE blood_type = ?
        ''', (blood_type,))
        
        stock, min_stock = cursor.fetchone()
        
        if stock < min_stock:
            # Registrar alerta
            cursor.execute("SELECT id FROM users WHERE role = 'admin' AND is_active = 1")
            admins = cursor.fetchall()
            
            message = f"Estoque de {blood_type} está abaixo do mínimo: {stock} unidades (mínimo: {min_stock})"
            
            for admin_id, in admins:
                cursor.execute('''
                    INSERT INTO alerts (type, message, recipient_id, sent_date, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('low_stock', message, admin_id, datetime.now().isoformat(), 'sent'))
            
            self.conn.commit()
    
    def log_activity(self, message, level='INFO'):
        """Registra atividades no log do sistema"""
        if level == 'INFO':
            logging.info(f"{datetime.now()} - {message}")
        elif level == 'ERROR':
            logging.error(f"{datetime.now()} - {message}")
    
    def clear_screen(self):
        """Limpa a tela atual"""
        for widget in self.root.winfo_children():
            widget.destroy()
            
            
# %% Execução Principal
if __name__ == "__main__":
    root = tk.Tk()
    app = BloodBankSystem(root)
    root.mainloop()