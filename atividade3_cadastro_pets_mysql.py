import hashlib
import wx
import mysql.connector
from mysql.connector import Error

# Configure com a senha root que voce definiu no MySQL Installer.
MYSQL_HOST = "localhost"
MYSQL_USER = "root"
MYSQL_PASSWORD = "COLOQUE_SUA_SENHA_AQUI"
MYSQL_DATABASE = "sistema_pets"


def conectar_banco():
    """Cria o banco e as tabelas caso ainda nao existam."""
    admin = mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD
    )
    cur = admin.cursor()
    cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cur.close()
    admin.close()

    con = mysql.connector.connect(
        host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            login VARCHAR(100) NOT NULL UNIQUE,
            hash_senha CHAR(64) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            idade INT NOT NULL,
            raca VARCHAR(100) NOT NULL,
            peso DECIMAL(7,2) NOT NULL,
            cor VARCHAR(100) NOT NULL,
            situacao VARCHAR(20) NOT NULL DEFAULT 'Tenho'
        )
    """)
    con.commit()
    cur.close()
    return con


def hash_senha(senha):
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def criar_usuario_inicial():
    """O sistema possui uma unica conta: admin / 1234."""
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM usuario")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO usuario (login, hash_senha) VALUES (%s, %s)",
            ("admin", hash_senha("1234"))
        )
    con.commit()
    cur.close()
    con.close()


def validar_login(login, senha):
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("SELECT hash_senha FROM usuario WHERE login = %s", (login,))
    linha = cur.fetchone()
    cur.close()
    con.close()
    return linha is not None and linha[0] == hash_senha(senha)


def alterar_senha(login, senha_nova):
    con = conectar_banco()
    cur = con.cursor()
    cur.execute(
        "UPDATE usuario SET hash_senha = %s WHERE login = %s",
        (hash_senha(senha_nova), login)
    )
    con.commit()
    alterou = cur.rowcount > 0
    cur.close()
    con.close()
    return alterou


def listar_pets():
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("""
        SELECT id, nome, idade, raca, peso, cor, situacao
        FROM pets ORDER BY id DESC
    """)
    dados = cur.fetchall()
    cur.close()
    con.close()
    return dados


def inserir_pet(dados):
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO pets (nome, idade, raca, peso, cor, situacao)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, dados)
    con.commit()
    cur.close()
    con.close()


def editar_pet(pet_id, dados):
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("""
        UPDATE pets
        SET nome=%s, idade=%s, raca=%s, peso=%s, cor=%s, situacao=%s
        WHERE id=%s
    """, dados + (pet_id,))
    con.commit()
    cur.close()
    con.close()


def apagar_pet(pet_id):
    con = conectar_banco()
    cur = con.cursor()
    cur.execute("DELETE FROM pets WHERE id=%s", (pet_id,))
    con.commit()
    cur.close()
    con.close()


class JanelaAlterarSenha(wx.Frame):
    def __init__(self, login):
        super().__init__(None, title="Alterar senha", size=(400, 260))
        self.login = login
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(30, 50, 70))

        titulo = wx.StaticText(panel, label="Alterar senha")
        titulo.SetForegroundColour(wx.WHITE)
        titulo.SetFont(wx.Font(18, wx.FONTFAMILY_ROMAN,
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.nova = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        self.confirmar = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        botao = wx.Button(panel, label="Salvar senha")
        botao.Bind(wx.EVT_BUTTON, self.salvar)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(titulo, 0, wx.ALL | wx.CENTER, 15)
        s.Add(wx.StaticText(panel, label="Nova senha"), 0, wx.LEFT | wx.TOP, 12)
        s.Add(self.nova, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        s.Add(wx.StaticText(panel, label="Confirme a senha"), 0, wx.LEFT | wx.TOP, 12)
        s.Add(self.confirmar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 12)
        s.Add(botao, 0, wx.ALL | wx.CENTER, 15)
        panel.SetSizer(s)
        self.Centre()

    def salvar(self, evento):
        nova = self.nova.GetValue()
        confirmacao = self.confirmar.GetValue()
        if not nova or not confirmacao:
            wx.MessageBox("Preencha os dois campos.", "Atenção",
                          wx.OK | wx.ICON_WARNING)
            return
        if nova != confirmacao:
            wx.MessageBox("As senhas não conferem.", "Erro",
                          wx.OK | wx.ICON_ERROR)
            return
        alterar_senha(self.login, nova)
        wx.MessageBox("Senha alterada com sucesso!", "Sucesso",
                      wx.OK | wx.ICON_INFORMATION)
        self.Close()


class JanelaLogin(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Cadastro de Pets", size=(430, 330))
        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(30, 50, 70))

        titulo = wx.StaticText(panel, label="Sistema de Cadastro de Pets")
        titulo.SetForegroundColour(wx.WHITE)
        titulo.SetFont(wx.Font(18, wx.FONTFAMILY_ROMAN,
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.login = wx.TextCtrl(panel)
        self.senha = wx.TextCtrl(panel, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        entrar = wx.Button(panel, label="Entrar")
        alterar = wx.Button(panel, label="Alterar senha")
        entrar.Bind(wx.EVT_BUTTON, self.entrar)
        self.senha.Bind(wx.EVT_TEXT_ENTER, self.entrar)
        alterar.Bind(wx.EVT_BUTTON, self.abrir_alteracao)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(titulo, 0, wx.ALL | wx.CENTER, 20)
        s.Add(wx.StaticText(panel, label="Login"), 0, wx.LEFT | wx.TOP, 15)
        s.Add(self.login, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        s.Add(wx.StaticText(panel, label="Senha"), 0, wx.LEFT | wx.TOP, 12)
        s.Add(self.senha, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 15)
        s.Add(entrar, 0, wx.ALL | wx.CENTER, 12)
        s.Add(alterar, 0, wx.BOTTOM | wx.CENTER, 10)
        panel.SetSizer(s)
        self.Centre()

    def entrar(self, evento):
        login = self.login.GetValue().strip()
        senha = self.senha.GetValue()
        if not login or not senha:
            wx.MessageBox("Informe login e senha.", "Atenção",
                          wx.OK | wx.ICON_WARNING)
            return
        if validar_login(login, senha):
            self.Hide()
            JanelaPets(self, login).Show()
        else:
            wx.MessageBox("Login ou senha incorretos.", "Erro",
                          wx.OK | wx.ICON_ERROR)
            self.senha.Clear()

    def abrir_alteracao(self, evento):
        login = self.login.GetValue().strip()
        senha = self.senha.GetValue()
        if not login or not validar_login(login, senha):
            wx.MessageBox("Informe login e senha atuais antes de alterar.",
                          "Atenção", wx.OK | wx.ICON_WARNING)
            return
        JanelaAlterarSenha(login).Show()


class JanelaPets(wx.Frame):
    def __init__(self, janela_login, login):
        super().__init__(None, title="Meus Pets - Histórico", size=(900, 590))
        self.janela_login = janela_login
        self.login = login
        self.pet_id = None

        panel = wx.Panel(self)
        panel.SetBackgroundColour(wx.Colour(30, 50, 70))
        titulo = wx.StaticText(panel, label=f"Meus Pets - Usuário: {login}")
        titulo.SetForegroundColour(wx.WHITE)
        titulo.SetFont(wx.Font(18, wx.FONTFAMILY_ROMAN,
                              wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        self.nome = wx.TextCtrl(panel)
        self.idade = wx.SpinCtrl(panel, min=0, max=150, initial=0)
        self.raca = wx.TextCtrl(panel)
        self.peso = wx.TextCtrl(panel)
        self.cor = wx.TextCtrl(panel)
        self.situacao = wx.Choice(panel, choices=["Tenho", "Tive"])
        self.situacao.SetSelection(0)

        self.lista = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        colunas = [("ID", 45), ("Nome", 130), ("Idade", 60),
                   ("Raça", 120), ("Peso (kg)", 85), ("Cor", 100),
                   ("Situação", 85)]
        for i, (nome_coluna, largura) in enumerate(colunas):
            self.lista.InsertColumn(i, nome_coluna, width=largura)
        self.lista.Bind(wx.EVT_LIST_ITEM_SELECTED, self.selecionar)

        salvar = wx.Button(panel, label="Cadastrar")
        atualizar = wx.Button(panel, label="Atualizar")
        excluir = wx.Button(panel, label="Excluir")
        limpar = wx.Button(panel, label="Limpar")
        sair = wx.Button(panel, label="Sair")
        salvar.Bind(wx.EVT_BUTTON, self.cadastrar)
        atualizar.Bind(wx.EVT_BUTTON, self.atualizar)
        excluir.Bind(wx.EVT_BUTTON, self.excluir)
        limpar.Bind(wx.EVT_BUTTON, self.limpar)
        sair.Bind(wx.EVT_BUTTON, self.sair)

        grade = wx.FlexGridSizer(3, 4, 8, 8)
        campos = [
            ("Nome", self.nome), ("Idade (anos)", self.idade),
            ("Raça", self.raca), ("Peso (kg)", self.peso),
            ("Cor", self.cor), ("Situação", self.situacao)
        ]
        for rotulo, controle in campos:
            grade.Add(wx.StaticText(panel, label=rotulo), 0, wx.ALIGN_CENTER_VERTICAL)
            grade.Add(controle, 1, wx.EXPAND)
        grade.AddGrowableCol(1, 1)
        grade.AddGrowableCol(3, 1)

        botoes = wx.BoxSizer(wx.HORIZONTAL)
        for b in (salvar, atualizar, excluir, limpar, sair):
            botoes.Add(b, 0, wx.ALL, 4)

        s = wx.BoxSizer(wx.VERTICAL)
        s.Add(titulo, 0, wx.ALL | wx.CENTER, 12)
        s.Add(grade, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 14)
        s.Add(botoes, 0, wx.CENTER | wx.TOP, 8)
        s.Add(self.lista, 1, wx.EXPAND | wx.ALL, 12)
        panel.SetSizer(s)
        self.Bind(wx.EVT_CLOSE, self.ao_fechar)
        self.Centre()
        self.recarregar()

    def dados_formulario(self):
        nome = self.nome.GetValue().strip()
        raca = self.raca.GetValue().strip()
        peso_texto = self.peso.GetValue().strip().replace(",", ".")
        cor = self.cor.GetValue().strip()
        situacao = self.situacao.GetStringSelection()

        if not nome or not raca or not peso_texto or not cor:
            wx.MessageBox("Preencha nome, raça, peso e cor.", "Atenção",
                          wx.OK | wx.ICON_WARNING)
            return None
        try:
            peso = float(peso_texto)
            if peso <= 0:
                raise ValueError
        except ValueError:
            wx.MessageBox("Peso deve ser um número maior que zero.",
                          "Peso inválido", wx.OK | wx.ICON_WARNING)
            return None
        return (nome, self.idade.GetValue(), raca, peso, cor, situacao)

    def cadastrar(self, evento):
        dados = self.dados_formulario()
        if dados is None:
            return
        inserir_pet(dados)
        self.recarregar()
        self.limpar(None)
        wx.MessageBox("Pet cadastrado!", "Sucesso", wx.OK | wx.ICON_INFORMATION)

    def recarregar(self):
        self.lista.DeleteAllItems()
        for pet in listar_pets():
            pet_id, nome, idade, raca, peso, cor, situacao = pet
            i = self.lista.InsertItem(self.lista.GetItemCount(), str(pet_id))
            valores = [nome, str(idade), raca, f"{float(peso):.2f}", cor, situacao]
            for coluna, valor in enumerate(valores, start=1):
                self.lista.SetItem(i, coluna, valor)

    def selecionar(self, evento):
        i = evento.GetIndex()
        self.pet_id = int(self.lista.GetItemText(i, 0))
        self.nome.SetValue(self.lista.GetItemText(i, 1))
        self.idade.SetValue(int(self.lista.GetItemText(i, 2)))
        self.raca.SetValue(self.lista.GetItemText(i, 3))
        self.peso.SetValue(self.lista.GetItemText(i, 4))
        self.cor.SetValue(self.lista.GetItemText(i, 5))
        self.situacao.SetSelection(
            0 if self.lista.GetItemText(i, 6) == "Tenho" else 1
        )

    def atualizar(self, evento):
        if self.pet_id is None:
            wx.MessageBox("Selecione um pet na lista.", "Atenção",
                          wx.OK | wx.ICON_WARNING)
            return
        dados = self.dados_formulario()
        if dados is None:
            return
        editar_pet(self.pet_id, dados)
        self.recarregar()
        self.limpar(None)
        wx.MessageBox("Registro atualizado!", "Sucesso",
                      wx.OK | wx.ICON_INFORMATION)

    def excluir(self, evento):
        if self.pet_id is None:
            wx.MessageBox("Selecione um pet na lista.", "Atenção",
                          wx.OK | wx.ICON_WARNING)
            return
        resposta = wx.MessageBox("Deseja excluir este registro?",
                                 "Confirmar", wx.YES_NO | wx.ICON_QUESTION)
        if resposta == wx.YES:
            apagar_pet(self.pet_id)
            self.recarregar()
            self.limpar(None)

    def limpar(self, evento):
        self.pet_id = None
        self.nome.Clear()
        self.idade.SetValue(0)
        self.raca.Clear()
        self.peso.Clear()
        self.cor.Clear()
        self.situacao.SetSelection(0)
        self.lista.UnselectAll()

    def sair(self, evento):
        self.Close()

    def ao_fechar(self, evento):
        self.janela_login.Show()
        evento.Skip()


if __name__ == "__main__":
    app = wx.App(False)
    try:
        criar_usuario_inicial()
        JanelaLogin().Show()
        app.MainLoop()
    except Error as erro:
        wx.MessageBox(
            "Falha ao conectar ao MySQL. Confira se o servidor esta iniciado "
            "e se a senha em MYSQL_PASSWORD esta correta.\n\n"
            f"Detalhes: {erro}",
            "Erro de banco de dados", wx.OK | wx.ICON_ERROR
        )
