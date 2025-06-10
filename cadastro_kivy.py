from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
import sqlite3

class LoginScreen(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = 15
        self.padding = [50, 20]

        # Título
        self.add_widget(Label(
            text="Banco de Sangue",
            font_size=30,
            color=(0.8, 0, 0, 1)  # Vermelho
        ))

        # Campos de entrada
        self.usuario = TextInput(
            hint_text="Usuário",
            size_hint=(1, 0.1),
            multiline=False
        )
        self.add_widget(self.usuario)

        self.senha = TextInput(
            hint_text="Senha",
            password=True,  # Esconde a senha
            size_hint=(1, 0.1),
            multiline=False
        )
        self.add_widget(self.senha)

        # Botão de login
        self.botao_login = Button(
            text="Entrar",
            size_hint=(1, 0.2),
            background_color=(0.8, 0, 0, 1),  # Vermelho
            color=(1, 1, 1, 1)  # Texto branco
        )
        self.botao_login.bind(on_press=self.verificar_login)
        self.add_widget(self.botao_login)

    def verificar_login(self, instance):
        usuario = self.usuario.text
        senha = self.senha.text

        # Verifica no banco de dados
        try:
            conn = sqlite3.connect("banco.db")
            cursor = conn.cursor()
            cursor.execute("SELECT perfil FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
            resultado = cursor.fetchone()
            conn.close()

            if resultado:
                perfil = resultado[0]
                self.mostrar_popup("Sucesso", f"Bem-vindo, {perfil}!")
                
                # Redireciona para a tela apropriada
                if perfil == "Admin":
                    print("Abrir menu_admin.py...")
                elif perfil == "Médico":
                    print("Abrir menu_medico.py...")
            else:
                self.mostrar_popup("Erro", "Usuário ou senha inválidos!")
        except sqlite3.Error as e:
            self.mostrar_popup("Erro", f"Erro no banco de dados: {str(e)}")

    def mostrar_popup(self, titulo, mensagem):
        popup = Popup(
            title=titulo,
            content=Label(text=mensagem),
            size_hint=(0.7, 0.4)
        )
        popup.open()

class BancoDeSangueApp(App):
    def build(self):
        return LoginScreen()

if __name__ == "__main__":
    BancoDeSangueApp().run()