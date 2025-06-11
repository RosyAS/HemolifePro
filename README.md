# hemolifepro

**Sistema Inteligente de Gestão de Estoque de Sangue – Maternidade Irene Neto**

Este projeto foi desenvolvido para informatizar o controle de bancos de sangue hospitalares, com foco na segurança, eficiência e antecipação da escassez. O sistema é prático, visual, validado, e já possui uma base sólida de funcionalidades que funcionam localmente.

---

## 👥 Atores do Sistema

| Ator                | Permissões                                                                 |
|---------------------|----------------------------------------------------------------------------|
| **Chefe de Secção** | Gerencia usuários, visualiza relatórios, configura alertas e sistema       |
| **Técnico**         | Registra doações, visualiza e retira bolsas, aprova ou rejeita requisições |
| **Médico**          | Realiza requisições de sangue e acompanha o status delas                   |

---

## 🧭 Estrutura do Sistema

- **Login seguro**
  - Cada ator entra com suas credenciais
- **Menu principal com navegação simples**
  - Acesso por botões: Doadores, Estoque, Requisições, Relatórios, Configurações
- **Cadastros**
  - Doadores: Nome, tipo sanguíneo, BI (único)
  - Usuários do sistema: Por perfil
- **Estoque de sangue**
  - Visual por tipo, com alertas visuais e sonoros
- **Requisições médicas**
  - Feitas pelo médico
  - Técnicos aprovam ou rejeitam
  - Aprovadas somem da lista
  - Rejeitadas vão para o histórico
- **Relatórios em PDF**
  - Por tipo sanguíneo, datas, ações, doações e movimentações
- **Chatbot simples**
  - Informa sobre o funcionamento do sistema e conceitos básicos
- **Previsão de demanda**
  - Estimativa baseada nos últimos 30 dias

---

## ✅ Funcionalidades Implementadas

- Login com autenticação
- Cadastro e validação de doadores (BI obrigatório)
- Registro de doações com controle de quantidade
- Estoque por tipo de sangue
- Alerta visual e sonoro de estoque baixo
- Controle de requisições (com aprovar/rejeitar)
- Relatórios automáticos em PDF
- Previsão de demanda (30 dias)
- Chatbot funcional
- Histórico de movimentações
- Interface gráfica feita com Tkinter

---

## 🧠 Tecnologias Utilizadas

- **Python 3**  
- **Tkinter** (interface)
- **SQLite** (banco local)
- **FPDF** (relatórios)
- **Algoritmos de estatística simples**
- **Sistema de alerta visual e sonoro**

---

## 🔧 Melhorias em Desenvolvimento

- Interface nova com **Kivy**
- **Validação avançada de BI** (não permitir múltiplos tipos por doador)
- Integração com banco **Supabase**
- Leitura com **código de barras real**
- **Chatbot com IA (DeepSeek)**
- Previsão com IA baseada nos **últimos 7 dias**
- Recuperação de senha por e-mail
- Alertas por **e-mail e SMS**
- Tela de configurações com backup e personalização

---

## 📌 Observações

O sistema já está em uso local com todas as funções essenciais, e com melhorias sendo implementadas. Ele foi planejado com base em necessidades reais de maternidades e pode ser expandido para outras instituições hospitalares.

---

## 🗂️ Esquema Resumido de Telas

[Login]
↓
[Menu Principal]
├─ Cadastro de Doadores
├─ Controle de Estoque
├─ Requisições Médicas
├─ Relatórios PDF
├─ Alertas
└─ Configurações do Sistema
## 👩‍💻 Desenvolvido por

**Rosa Somaquesendje**  
Estudante de Engenharia Informática  

