import sqlite3

# Conectar ao banco
conn = sqlite3.connect('banco.db')
cursor = conn.cursor()

# Criar tabela de usuários
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    senha TEXT NOT NULL,
    perfil TEXT NOT NULL -- Admin, Tecnico, Medico
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS bolsas_sangue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_doador TEXT NOT NULL,
    tipo TEXT NOT NULL,
    codigo_barras TEXT UNIQUE NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS requisicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_medico TEXT NOT NULL,
    tipo_sangue TEXT NOT NULL,
    quantidade INTEGER NOT NULL,
    status TEXT DEFAULT 'pendente',
    data TEXT DEFAULT CURRENT_TIMESTAMP
)
""")


# Inserir usuários de exemplo
cursor.execute("INSERT OR IGNORE INTO usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
               ("Administrador Geral", "admin", "admin123", "Admin"))

cursor.execute("INSERT OR IGNORE INTO usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
               ("Técnico João", "tecnico", "tec123", "Tecnico"))

cursor.execute("INSERT OR IGNORE INTO usuarios (nome, usuario, senha, perfil) VALUES (?, ?, ?, ?)",
               ("Dra. Maria", "medico", "med123", "Medico"))

conn.commit()
conn.close()

print("Banco criado com sucesso.")
