#!/usr/bin/env python3
"""
gui_openalex.py

Interface gráfica (Tkinter) para openalex_colab.py.
Permite rodar a análise de grafo de colaboração sem tocar no terminal.

Visual: tema Sun Valley (pacote sv-ttk, aparência do Windows 11) com modo
claro/escuro. Sem o sv-ttk instalado, cai para um tema "clam" estilizado.

Uso:
  python3 gui_openalex.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import subprocess
import sys
import os
import re
import threading
import traceback
from pathlib import Path

# Importado no topo para que o PyInstaller inclua o módulo no executável.
import openalex_colab

try:
    import sv_ttk  # tema Sun Valley (Windows 11)
except ImportError:
    sv_ttk = None

# ------------------------------------------------------------
# Áreas de conhecimento sugeridas (mesma lista do openalex_colab)
# ------------------------------------------------------------
OPENALEX_COMMON_FIELDS = [
    "Agricultural and Biological Sciences",
    "Arts and Humanities",
    "Biochemistry, Genetics and Molecular Biology",
    "Business, Management and Accounting",
    "Chemical Engineering",
    "Chemistry",
    "Computer Science",
    "Decision Sciences",
    "Dentistry",
    "Earth and Planetary Sciences",
    "Economics, Econometrics and Finance",
    "Education",
    "Energy",
    "Engineering",
    "Environmental Science",
    "Health Professions",
    "Immunology and Microbiology",
    "Library and Information Science",
    "Materials Science",
    "Mathematics",
    "Medicine",
    "Neuroscience",
    "Nursing",
    "Pharmacology, Toxicology and Pharmaceutics",
    "Physics and Astronomy",
    "Psychology",
    "Social Sciences",
    "Veterinary",
]

OPENALEX_BASE = "https://api.openalex.org"

# ------------------------------------------------------------
# Paletas de cores (claro / escuro)
# ------------------------------------------------------------
# Os widgets ttk recebem as cores do tema; estas paletas cobrem o que o tema
# não pinta sozinho (cabeçalho, listas, console de log, textos secundários).
PALETTES = {
    "light": {
        "bg": "#fafafa", "card": "#ffffff", "border": "#e3e6ea",
        "text": "#1b1f24", "muted": "#5f6b7a", "accent": "#005fb8",
        "accent_soft": "#e6f0fa", "success": "#0f7b3f", "danger": "#c42b1c",
        "header_bg": "#0b3a6e", "header_fg": "#ffffff", "header_sub": "#b9d3f0",
        "list_bg": "#ffffff", "list_fg": "#1b1f24", "select_bg": "#005fb8", "select_fg": "#ffffff",
        "console_bg": "#1e1e1e", "console_fg": "#d4d4d4",
    },
    "dark": {
        "bg": "#1c1c1c", "card": "#2b2b2b", "border": "#3a3a3a",
        "text": "#f3f3f3", "muted": "#a3abb5", "accent": "#57c8ff",
        "accent_soft": "#1f3446", "success": "#6ccb5f", "danger": "#ff99a4",
        "header_bg": "#0e2238", "header_fg": "#ffffff", "header_sub": "#8fb3d9",
        "list_bg": "#2b2b2b", "list_fg": "#f3f3f3", "select_bg": "#2f6fb0", "select_fg": "#ffffff",
        "console_bg": "#141414", "console_fg": "#d4d4d4",
    },
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_results_dir() -> Path:
    d = get_app_dir() / "resultados"
    d.mkdir(exist_ok=True)
    return d


def _enable_windows_dpi_awareness():
    """Sem isto, o Windows "estica" a janela em telas com escala >100% e as
    fontes ficam borradas."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def _set_windows_titlebar_dark(window: tk.Misc, dark: bool):
    """Deixa a barra de título do Windows 10/11 escura junto com o tema."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (20; 19 em builds antigas)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value), 4) == 0:
                break
    except Exception:
        pass


class TextRedirector:
    """
    Redireciona stdout/stderr para um widget Text do Tkinter (thread-safe).
    Se on_line for informado, é chamado (na thread da interface) para cada
    linha completa -- usado para atualizar a barra de progresso.
    """

    def __init__(self, widget: tk.Text, on_line=None):
        self.widget = widget
        self.on_line = on_line
        self._buffer = ""

    def write(self, text: str):
        if not text:
            return
        self.widget.after(0, self._insert, text)
        if self.on_line:
            self._buffer += text
            *lines, self._buffer = self._buffer.split("\n")
            for line in lines:
                self.widget.after(0, self.on_line, line)

    def _insert(self, text: str):
        try:
            self.widget.configure(state=tk.NORMAL)
            tag = "error" if ("Erro" in text or "Traceback" in text) else None
            self.widget.insert(tk.END, text, tag)
            self.widget.see(tk.END)
            self.widget.configure(state=tk.DISABLED)
        except tk.TclError:
            pass

    def flush(self):
        pass


# ------------------------------------------------------------
# Verificador de dependências
# ------------------------------------------------------------

class DependencyInstaller:

    DEPENDENCIES = {
        "requests": "requests",
        "networkx": "networkx",
        "community": "python-louvain",
        "pyvis": "pyvis",
        "matplotlib": "matplotlib",
    }

    @staticmethod
    def check_and_install(root: tk.Tk) -> bool:
        if getattr(sys, "frozen", False):
            return True

        missing = [
            (mod, pkg)
            for mod, pkg in DependencyInstaller.DEPENDENCIES.items()
            if not _can_import(mod)
        ]
        if not missing:
            return True

        msg = "Dependências faltando:\n\n"
        msg += "\n".join(f"  • {pkg} (módulo: {mod})" for mod, pkg in missing)
        msg += "\n\nDeseja instalar automaticamente agora?"

        if messagebox.askyesno("Dependências", msg):
            return DependencyInstaller._install(missing, root)

        messagebox.showerror(
            "Dependências",
            "Não é possível continuar sem as dependências.\n\n"
            "Para instalar manualmente:\n"
            "pip install -r requirements.txt",
        )
        return False

    @staticmethod
    def _install(packages, root: tk.Tk) -> bool:
        win = tk.Toplevel(root)
        win.title("Instalando Dependências")
        win.geometry("520x320")

        ttk.Label(win, text="Instalando pacotes...", font=("Segoe UI", 12)).pack(pady=15)
        bar = ttk.Progressbar(win, mode="indeterminate")
        bar.pack(pady=5, padx=20, fill=tk.X)
        bar.start()
        txt = tk.Text(win, height=10, width=62)
        txt.pack(pady=8, padx=10, fill=tk.BOTH, expand=True)
        win.update()

        cmd = [sys.executable, "-m", "pip", "install"] + [p for _, p in packages]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            txt.insert(tk.END, result.stdout)
            if result.returncode != 0:
                txt.insert(tk.END, f"\nErro:\n{result.stderr}")
                messagebox.showerror("Instalação", "Erro ao instalar dependências.")
                win.destroy()
                return False
            txt.insert(tk.END, "\n✓ Instalação concluída!")
        except Exception as exc:
            txt.insert(tk.END, f"Erro: {exc}")
            messagebox.showerror("Instalação", f"Erro: {exc}")
            win.destroy()
            return False

        win.after(2500, win.destroy)
        return True


def _can_import(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


# ------------------------------------------------------------
# Interface principal
# ------------------------------------------------------------

class OpenAlexGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SciCollab-BR — Grafo de Colaboração Científica")
        self.root.resizable(True, True)

        self.results_dir = get_results_dir()
        self.output_files: list[str] = []

        # Estado da busca de instituições
        self._inst_results: list[dict] = []   # resultados da API
        self._selected_inst: dict = {}         # {"id": ..., "name": ...}

        # Widgets tk "puros" (não-ttk) que precisam ser repintados ao trocar
        # de tema: lista de (widget, papel)
        self._themed: list[tuple[tk.Misc, str]] = []
        self.mode = "light"
        self.pal = PALETTES[self.mode]

        self._setup_fonts()
        # O sv-ttk chama tk_setPalette a cada <<ThemeChanged>>, o que pinta por
        # cima as cores do cabeçalho/listas -- repinta logo depois (uma vez só:
        # o evento chega para cada widget da janela).
        self._repaint_pending = False
        self.root.bind("<<ThemeChanged>>", lambda e: self._schedule_repaint(), add="+")
        self._apply_theme(self.mode)
        self._build_ui()
        self._repaint_tk_widgets()
        self._place_main_window(920, 880)

    # ----------------------------------------------------------
    # Tema, fontes e cores
    # ----------------------------------------------------------

    def _px(self, n: int) -> int:
        """Converte pixels "lógicos" (96 dpi) para a escala real da tela."""
        return int(n * self.root.winfo_fpixels("1i") / 96)

    def _place_main_window(self, width: int, height: int):
        w, h = self._px(width), self._px(height)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        w, h = min(w, sw - 40), min(h, sh - 80)
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 20)}")
        self.root.minsize(self._px(720), self._px(560))

    def _setup_fonts(self):
        family = "Segoe UI" if "Segoe UI" in tkfont.families() else "Helvetica"
        mono = "Cascadia Mono" if "Cascadia Mono" in tkfont.families() else "Consolas"
        self.f_body = (family, 10)
        self.f_small = (family, 9)
        self.f_bold = (family, 10, "bold")
        self.f_section = (family, 12, "bold")
        self.f_title = (family, 18, "bold")
        self.f_subtitle = (family, 10)
        self.f_mono = (mono, 9)
        tkfont.nametofont("TkDefaultFont").configure(family=family, size=10)
        tkfont.nametofont("TkTextFont").configure(family=family, size=10)

    def _apply_theme(self, mode: str):
        self.mode = mode
        self.pal = p = PALETTES[mode]
        style = ttk.Style(self.root)

        if sv_ttk is not None:
            sv_ttk.set_theme(mode)
            # O sv-ttk só aplica as cores-base (fundo, fonte...) ao processar o
            # evento <<ThemeChanged>> -- que, na primeira troca, ainda não foi
            # entregue. Aplica agora para não nascer com o fundo cinza do "clam".
            self.root.tk.call("configure_colors")
        else:
            # Fallback sem sv-ttk: "clam" com as cores da paleta
            style.theme_use("clam")
            style.configure(".", background=p["bg"], foreground=p["text"], fieldbackground=p["card"],
                            bordercolor=p["border"], font=self.f_body)
            style.configure("Card.TFrame", background=p["card"], relief="solid", borderwidth=1)
            style.configure("TButton", padding=(12, 6))
            style.configure("Accent.TButton", background=p["accent"], foreground="#ffffff", padding=(16, 8))
            style.map("Accent.TButton", background=[("active", p["accent"])])
            style.configure("TCheckbutton", background=p["card"])

        card_bg = p["card"] if sv_ttk is None else None
        label_opts = {"background": card_bg} if card_bg else {}
        style.configure("Section.TLabel", font=self.f_section, foreground=p["text"], **label_opts)
        style.configure("Body.TLabel", font=self.f_body, foreground=p["text"], **label_opts)
        style.configure("Bold.TLabel", font=self.f_bold, foreground=p["text"], **label_opts)
        style.configure("Hint.TLabel", font=self.f_small, foreground=p["muted"], **label_opts)
        style.configure("Tag.TLabel", font=self.f_small, foreground=p["muted"], **label_opts)
        style.configure("Selected.TLabel", font=self.f_bold, foreground=p["accent"], **label_opts)
        style.configure("Status.TLabel", font=self.f_body, foreground=p["muted"])
        style.configure("Success.TLabel", font=self.f_section, foreground=p["success"])
        style.configure("Danger.TLabel", font=self.f_section, foreground=p["danger"])

        self.root.configure(background=p["bg"])
        _set_windows_titlebar_dark(self.root, mode == "dark")

    def _themed_widget(self, widget, role: str):
        """Registra um widget tk para ser repintado ao trocar o tema."""
        self._themed.append((widget, role))
        return widget

    def _schedule_repaint(self):
        if not self._repaint_pending:
            self._repaint_pending = True
            self.root.after_idle(self._repaint_tk_widgets)

    def _repaint_tk_widgets(self):
        self._repaint_pending = False
        p = self.pal
        alive = []
        for w, role in self._themed:
            try:
                if role == "list":
                    w.configure(bg=p["list_bg"], fg=p["list_fg"], selectbackground=p["select_bg"],
                                selectforeground=p["select_fg"], highlightbackground=p["border"],
                                highlightcolor=p["accent"], disabledforeground=p["muted"])
                elif role == "console":
                    w.configure(bg=p["console_bg"], fg=p["console_fg"], insertbackground=p["console_fg"])
                    w.tag_configure("error", foreground="#f48771")
                elif role == "text":
                    w.configure(bg=p["card"], fg=p["text"])
                elif role == "canvas":
                    w.configure(bg=p["bg"])
                elif role == "header":
                    w.configure(bg=p["header_bg"])
                elif role == "header_title":
                    w.configure(bg=p["header_bg"], fg=p["header_fg"])
                elif role == "header_sub":
                    w.configure(bg=p["header_bg"], fg=p["header_sub"])
                elif role == "badge":
                    w.configure(bg=p["accent"], fg=p["card"] if self.mode == "dark" else "#ffffff")
                elif role == "chip":
                    w.configure(bg=p["accent_soft"], fg=p["accent"])
                alive.append((w, role))
            except tk.TclError:
                pass  # widget já destruído (ex: janela fechada)
        self._themed = alive

    def _toggle_theme(self):
        self._apply_theme("dark" if self.mode == "light" else "light")
        self._repaint_tk_widgets()
        self._theme_btn.configure(text="☀  Tema claro" if self.mode == "dark" else "☾  Tema escuro")

    # ----------------------------------------------------------
    # Construção da interface
    # ----------------------------------------------------------

    def _build_ui(self):
        self._build_header()

        # Barra inferior de ações (empacotada antes do conteúdo para ficar
        # sempre visível, mesmo com a janela pequena)
        footer = ttk.Frame(self.root, padding=(24, 12))
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(self.root, orient="horizontal").pack(side=tk.BOTTOM, fill=tk.X)

        ttk.Button(
            footer, text="▶   Executar análise", style="Accent.TButton", command=self._run,
        ).pack(side=tk.RIGHT, ipadx=self._px(10), ipady=self._px(2))
        ttk.Button(footer, text="Ver resultados", command=self._open_results).pack(side=tk.LEFT)
        ttk.Button(footer, text="Ajuda", command=self._help).pack(side=tk.LEFT, padx=8)

        # Conteúdo rolável
        outer = ttk.Frame(self.root)
        outer.pack(fill=tk.BOTH, expand=True)

        self._canvas = self._themed_widget(tk.Canvas(outer, highlightthickness=0, bd=0), "canvas")
        vsb = ttk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._form_frame = ttk.Frame(self._canvas, padding=(24, 16, 24, 24))

        self._form_frame.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        form_window = self._canvas.create_window((0, 0), window=self._form_frame, anchor="nw")
        # Mantém o formulário esticado na largura total do canvas — sem isso,
        # ao maximizar/redimensionar a janela o conteúdo fica ancorado à
        # esquerda com um vão vazio do lado (o canvas cresce, o frame não).
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfig(form_window, width=e.width),
        )
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Scroll do mouse só ativo enquanto o cursor está sobre este canvas
        # (bind local, não bind_all — evita vazar para outras janelas).
        self._canvas.bind(
            "<Enter>",
            lambda e: self._canvas.bind_all(
                "<MouseWheel>",
                lambda ev: self._canvas.yview_scroll(-1 * (ev.delta // 120), "units"),
            ),
        )
        self._canvas.bind("<Leave>", lambda e: self._canvas.unbind_all("<MouseWheel>"))

        self._build_form(self._form_frame)

    def _build_header(self):
        header = self._themed_widget(tk.Frame(self.root, padx=24, pady=18), "header")
        header.pack(fill=tk.X)

        text_box = self._themed_widget(tk.Frame(header), "header")
        text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._themed_widget(
            tk.Label(text_box, text="SciCollab-BR", font=self.f_title, anchor="w"), "header_title"
        ).pack(anchor=tk.W)
        self._themed_widget(
            tk.Label(
                text_box,
                text="Redes de colaboração científica entre pesquisadores e universidades · dados do OpenAlex",
                font=self.f_subtitle, anchor="w",
            ),
            "header_sub",
        ).pack(anchor=tk.W, pady=(2, 0))

        self._theme_btn = ttk.Button(header, text="☾  Tema escuro", command=self._toggle_theme)
        self._theme_btn.pack(side=tk.RIGHT, anchor=tk.N)

    # helpers de layout ----------------------------------------

    def _section(self, parent, number: int, title: str, tag: str = "") -> ttk.Frame:
        """Cartão com número da etapa, título e etiqueta (ex: "opcional")."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=(18, 14, 18, 16))
        card.pack(fill=tk.X, pady=(0, 14))

        head = ttk.Frame(card, style="Card.TFrame" if sv_ttk is None else "TFrame")
        head.pack(fill=tk.X, pady=(0, 10))
        self._themed_widget(
            tk.Label(head, text=str(number), font=self.f_bold, width=2, padx=2, pady=0), "badge"
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(head, text=title, style="Section.TLabel").pack(side=tk.LEFT)
        if tag:
            ttk.Label(head, text=tag, style="Tag.TLabel").pack(side=tk.LEFT, padx=(10, 0), pady=(3, 0))
        return card

    def _hint(self, parent, text: str, **pack):
        lbl = ttk.Label(parent, text=text, style="Hint.TLabel")
        lbl.pack(anchor=tk.W, **pack)
        return lbl

    def _listbox(self, parent, height: int, **kw) -> tk.Listbox:
        """Listbox com borda fina e cores do tema, dentro de um frame com scrollbar."""
        frame = ttk.Frame(parent, style="Card.TFrame" if sv_ttk is None else "TFrame")
        frame.pack(fill=tk.X)
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        lb = tk.Listbox(
            frame, height=height, yscrollcommand=scroll.set, font=self.f_body,
            activestyle="none", relief="flat", bd=0, highlightthickness=1, **kw,
        )
        lb.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2)
        scroll.config(command=lb.yview)
        # roda do mouse rola só a lista (e não o formulário inteiro junto)
        lb.bind("<MouseWheel>", lambda ev: (lb.yview_scroll(-1 * (ev.delta // 120), "units"), "break")[1])
        return self._themed_widget(lb, "list")

    def _center_on_root(self, win: tk.Toplevel, width: int, height: int):
        """Centraliza uma janela secundária sobre a janela principal (em vez
        de deixá-la cair no canto da tela, parecendo um app separado)."""
        width, height = self._px(width), self._px(height)
        self.root.update_idletasks()
        rx, ry = self.root.winfo_x(), self.root.winfo_y()
        rw, rh = self.root.winfo_width(), self.root.winfo_height()
        x = rx + max(0, (rw - width) // 2)
        y = ry + max(0, (rh - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")
        win.configure(background=self.pal["bg"])
        win.transient(self.root)
        _set_windows_titlebar_dark(win, self.mode == "dark")

    # ----------------------------------------------------------
    # Formulário
    # ----------------------------------------------------------

    def _build_form(self, parent):
        self.fields: dict = {}

        self._build_institution_section(parent)
        self._build_topic_section(parent)
        self._build_period_section(parent)
        self._build_limits_section(parent)
        self._build_options_section(parent)

    # ---- Seção 1: Instituição --------------------------------

    def _build_institution_section(self, parent):
        sec = self._section(parent, 1, "Universidade / instituição", "obrigatório")

        search_row = ttk.Frame(sec, style="Card.TFrame" if sv_ttk is None else "TFrame")
        search_row.pack(fill=tk.X, pady=(0, 6))

        self._inst_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_row, textvariable=self._inst_search_var, font=self.f_body)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=self._px(2))
        search_entry.bind("<Return>", lambda e: self._search_institutions())

        self._inst_search_btn = ttk.Button(
            search_row, text="Buscar", style="Accent.TButton", command=self._search_institutions
        )
        self._inst_search_btn.pack(side=tk.LEFT, padx=(8, 0))

        self._hint(sec, "Digite o nome da universidade e pressione Enter — depois clique no resultado certo",
                   pady=(0, 8))

        self._inst_listbox = self._listbox(sec, height=5)
        self._inst_listbox.bind("<<ListboxSelect>>", self._on_institution_select)
        self._inst_listbox.insert(tk.END, "  Os resultados da busca aparecem aqui")
        self._inst_listbox.config(state=tk.DISABLED)

        # Instituição selecionada, em destaque
        sel_row = ttk.Frame(sec, style="Card.TFrame" if sv_ttk is None else "TFrame")
        sel_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(sel_row, text="Selecionada:", style="Hint.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self._inst_selected_var = tk.StringVar(value="nenhuma")
        self._inst_chip = self._themed_widget(
            tk.Label(sel_row, textvariable=self._inst_selected_var, font=self.f_bold,
                     padx=10, pady=3, anchor="w", justify="left"),
            "chip",
        )
        self._inst_chip.pack(side=tk.LEFT, fill=tk.X, expand=True)
        sel_row.bind("<Configure>", lambda e: self._inst_chip.configure(wraplength=max(200, e.width - 140)))

        # Campo oculto que guarda o nome para a análise
        self.fields["institution"] = tk.StringVar()

    # ---- Seção 2: Área de conhecimento -----------------------

    def _build_topic_section(self, parent):
        sec = self._section(parent, 2, "Área de conhecimento", "opcional — vazio = universidade inteira")

        self._hint(sec, "Clique para marcar uma ou mais áreas (clique de novo para desmarcar)", pady=(0, 6))

        self._topic_listbox = self._listbox(sec, height=7, selectmode=tk.MULTIPLE, exportselection=False)
        for field in OPENALEX_COMMON_FIELDS:
            self._topic_listbox.insert(tk.END, f"  {field}")

        ttk.Button(sec, text="Limpar seleção", command=self._clear_topic_sel).pack(anchor=tk.W, pady=(8, 12))

        ttk.Label(sec, text="Ou digite áreas livremente", style="Bold.TLabel").pack(anchor=tk.W)
        self._hint(sec, "Separe várias com ponto e vírgula. Ex: Bibliometrics; Information Systems",
                   pady=(0, 4))
        self.fields["topic"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["topic"]).pack(fill=tk.X, pady=(0, 12))

        ttk.Label(sec, text="Topic IDs diretos (avançado)", style="Bold.TLabel").pack(anchor=tk.W)
        self._hint(sec, "IDs do OpenAlex separados por vírgula (ex: T10712,T14330) — têm prioridade sobre o resto",
                   pady=(0, 4))
        self.fields["topic_id"] = tk.StringVar()
        ttk.Entry(sec, textvariable=self.fields["topic_id"]).pack(fill=tk.X)

    # ---- Seção 3: Período ------------------------------------

    def _build_period_section(self, parent):
        sec = self._section(parent, 3, "Período", "opcional")
        row = ttk.Frame(sec, style="Card.TFrame" if sv_ttk is None else "TFrame")
        row.pack(fill=tk.X)

        ttk.Label(row, text="De", style="Body.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        self.fields["year_from"] = tk.StringVar()
        ttk.Entry(row, textvariable=self.fields["year_from"], width=8).pack(side=tk.LEFT)

        ttk.Label(row, text="até", style="Body.TLabel").pack(side=tk.LEFT, padx=12)
        self.fields["year_to"] = tk.StringVar()
        ttk.Entry(row, textvariable=self.fields["year_to"], width=8).pack(side=tk.LEFT)

        self._hint(sec, "Ex: 2018 até 2024. Deixe em branco para considerar todos os anos", pady=(8, 0))

    # ---- Seção 4: Limites ------------------------------------

    def _build_limits_section(self, parent):
        sec = self._section(parent, 4, "Limites de coleta")
        grid = ttk.Frame(sec, style="Card.TFrame" if sv_ttk is None else "TFrame")
        grid.pack(fill=tk.X)
        grid.columnconfigure(2, weight=1)

        rows = [
            ("max_authors", "Máx. pesquisadores", 100, 1, 5000,
             "Os mais produtivos entram primeiro"),
            ("max_works", "Máx. publicações por pesquisador", 50, 1, 500,
             "Mais = mais completo, porém mais lento"),
            ("max_institutions", "Máx. instituições na rede", 100, 2, 2000,
             "As com mais publicações em comum"),
            ("max_authors_per_work", "Ignorar publicações com mais de … autores", 50, 0, 10000,
             "Autoria em massa — 0 = sem limite"),
        ]
        for r, (key, label, default, lo, hi, hint) in enumerate(rows):
            ttk.Label(grid, text=label, style="Body.TLabel").grid(row=r, column=0, sticky="w", pady=5)
            self.fields[key] = tk.IntVar(value=default)
            ttk.Spinbox(grid, from_=lo, to=hi, textvariable=self.fields[key], width=8).grid(
                row=r, column=1, sticky="w", padx=14, pady=5
            )
            ttk.Label(grid, text=hint, style="Hint.TLabel").grid(row=r, column=2, sticky="w", pady=5)

    # ---- Seção 5: Opções -------------------------------------

    def _build_options_section(self, parent):
        sec = self._section(parent, 5, "Opções")

        self.fields["restrict"] = tk.BooleanVar()
        ttk.Checkbutton(
            sec,
            text="Só colaborações internas (exclui coautores de fora da universidade)",
            variable=self.fields["restrict"],
            style="Switch.TCheckbutton" if sv_ttk is not None else "TCheckbutton",
        ).pack(anchor=tk.W, pady=(0, 2))
        self._hint(sec, "Vale para o grafo de pesquisadores; a rede entre instituições não é afetada",
                   pady=(0, 14))

        grid = ttk.Frame(sec, style="Card.TFrame" if sv_ttk is None else "TFrame")
        grid.pack(fill=tk.X)
        grid.columnconfigure(0, weight=1, uniform="opt")
        grid.columnconfigure(1, weight=1, uniform="opt")

        ttk.Label(grid, text="Nome dos arquivos de saída", style="Bold.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 12)
        )
        self.fields["output"] = tk.StringVar()
        out_entry = ttk.Entry(grid, textvariable=self.fields["output"])
        out_entry.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(4, 2))
        ttk.Label(grid, text="Padrão: grafo_colaboracao", style="Hint.TLabel").grid(
            row=2, column=0, sticky="w"
        )

        ttk.Label(grid, text="Seu e-mail (recomendado)", style="Bold.TLabel").grid(row=0, column=1, sticky="w")
        self.fields["email"] = tk.StringVar()
        ttk.Entry(grid, textvariable=self.fields["email"]).grid(row=1, column=1, sticky="ew", pady=(4, 2))
        ttk.Label(
            grid, text="Dá acesso à 'polite pool' do OpenAlex (menos erros 429)", style="Hint.TLabel"
        ).grid(row=2, column=1, sticky="w")

        self._hint(sec, f"Os arquivos serão salvos em:  {self.results_dir}", pady=(14, 0))

    # ----------------------------------------------------------
    # Busca de instituições (thread separada)
    # ----------------------------------------------------------

    def _search_institutions(self):
        query = self._inst_search_var.get().strip()
        if not query:
            messagebox.showinfo("Busca", "Digite um nome para buscar.")
            return

        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_listbox.insert(tk.END, "  Buscando…")
        self._inst_listbox.config(state=tk.DISABLED)
        self._inst_search_btn.config(state=tk.DISABLED)

        threading.Thread(
            target=self._fetch_institutions_thread, args=(query,), daemon=True
        ).start()

    def _fetch_institutions_thread(self, query: str):
        """
        Busca instituições com estratégia em camadas para maximizar os resultados:
          1. Autocomplete com a query original  (endpoint otimizado para busca parcial)
          2. Autocomplete com a query sem acentos/diacríticos
          3. Search normal com a query original  (fallback)
          4. Search normal sem acentos           (fallback final)
        """
        import requests
        import unicodedata

        def strip_accents(s: str) -> str:
            """Remove acentos e diacríticos: 'São Paulo' → 'Sao Paulo'."""
            return "".join(
                c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn"
            )

        def normalize(raw: list) -> list:
            """Uniformiza campos entre o retorno do autocomplete e do search."""
            out = []
            for r in raw:
                if "hint" in r:          # formato autocomplete
                    hint = r.get("hint", "")
                    # hint costuma ser "Cidade, PAÍS" ou só "PAÍS"
                    country = hint.rsplit(",", 1)[-1].strip() if "," in hint else hint.strip()
                    out.append({
                        "id":           r["id"],
                        "display_name": r["display_name"],
                        "country_code": country,
                        "works_count":  r.get("works_count", 0),
                    })
                else:                    # formato search normal
                    out.append(r)
            return out

        try:
            stripped = strip_accents(query)
            queries  = [query] if stripped == query else [query, stripped]

            results = []

            # Fase 1 e 2: autocomplete (mais tolerante a buscas parciais)
            for q in queries:
                resp = requests.get(
                    f"{OPENALEX_BASE}/autocomplete/institutions",
                    params={"q": q, "mailto": openalex_colab.POLITE_EMAIL},
                    timeout=12,
                )
                if resp.ok:
                    raw = resp.json().get("results", [])
                    if raw:
                        results = normalize(raw)
                        break

            # Fase 3 e 4: search normal (fallback)
            if not results:
                for q in queries:
                    resp = requests.get(
                        f"{OPENALEX_BASE}/institutions",
                        params={
                            "search":   q,
                            "per_page": 10,
                            "mailto":   openalex_colab.POLITE_EMAIL,
                        },
                        timeout=12,
                    )
                    if resp.ok:
                        raw = resp.json().get("results", [])
                        if raw:
                            results = normalize(raw)
                            break

            self.root.after(0, self._update_inst_listbox, results)

        except Exception as exc:
            self.root.after(0, self._inst_search_error, str(exc))

    def _update_inst_listbox(self, results: list):
        self._inst_results = results
        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_search_btn.config(state=tk.NORMAL)

        if not results:
            self._inst_listbox.insert(
                tk.END,
                "  Nenhum resultado. Tente o nome em inglês, sem abreviações ou sem acentos.",
            )
            return

        for r in results:
            country = r.get("country_code", "?")
            works   = r.get("works_count", 0)
            name    = r.get("display_name", "?")
            self._inst_listbox.insert(
                tk.END, f"  {name}   ·   {country}   ·   {works:,} publicações".replace(",", ".")
            )

    def _inst_search_error(self, msg: str):
        self._inst_listbox.config(state=tk.NORMAL)
        self._inst_listbox.delete(0, tk.END)
        self._inst_listbox.insert(tk.END, f"  Erro na busca: {msg}")
        self._inst_search_btn.config(state=tk.NORMAL)

    def _on_institution_select(self, event):
        sel = self._inst_listbox.curselection()
        if not sel or not self._inst_results:
            return
        idx = sel[0]
        if idx >= len(self._inst_results):
            return
        r = self._inst_results[idx]
        self._selected_inst = {"id": r["id"], "name": r["display_name"]}
        self.fields["institution"].set(r["display_name"])
        country = r.get("country_code", "?")
        works   = r.get("works_count", 0)
        self._inst_selected_var.set(
            f"✓  {r['display_name']}  ·  {country}  ·  {works:,} publicações".replace(",", ".")
        )

    # ----------------------------------------------------------
    # Helpers de formulário
    # ----------------------------------------------------------

    def _clear_topic_sel(self):
        self._topic_listbox.selection_clear(0, tk.END)

    def _validate(self) -> bool:
        if not self.fields["institution"].get().strip():
            messagebox.showerror(
                "Validação",
                "Selecione uma universidade usando a busca na etapa 1.",
            )
            return False
        for key in ("year_from", "year_to"):
            val = self.fields[key].get().strip()
            if val:
                try:
                    int(val)
                except ValueError:
                    messagebox.showerror("Validação", "O campo de ano deve ser um número inteiro.")
                    return False
        return True

    def _collect_params(self) -> dict:
        lb_sel    = [self._topic_listbox.get(i).strip() for i in self._topic_listbox.curselection()]
        txt_topics = [t.strip() for t in self.fields["topic"].get().split(";") if t.strip()]
        all_topics = lb_sel + [t for t in txt_topics if t not in lb_sel]

        return {
            "institution": self.fields["institution"].get().strip(),
            "institution_id": self._selected_inst.get("id", ""),
            "topic_id":    self.fields["topic_id"].get().strip(),
            "topic":       ";".join(all_topics),
            "year_from":   self.fields["year_from"].get().strip() or None,
            "year_to":     self.fields["year_to"].get().strip() or None,
            "max_authors": int(self.fields["max_authors"].get()),
            "max_works":   int(self.fields["max_works"].get()),
            "max_institutions": int(self.fields["max_institutions"].get()),
            "max_authors_per_work": int(self.fields["max_authors_per_work"].get()),
            "restrict":    bool(self.fields["restrict"].get()),
            "output":      self.fields["output"].get().strip() or "grafo_colaboracao",
            "email":       self.fields["email"].get().strip(),
        }

    # ----------------------------------------------------------
    # Execução da análise
    # ----------------------------------------------------------

    def _run(self):
        if not self._validate():
            return

        params = self._collect_params()

        # Se há termos de área (sem IDs diretos), mostra o diálogo de seleção
        # de topics antes de iniciar a análise, para que o usuário confirme
        # quais subtopics incluir.
        if params["topic"] and not params["topic_id"]:
            terms = [t.strip() for t in params["topic"].split(";") if t.strip()]
            self._fetch_topics_then_dialog(terms, params)
        else:
            # IDs diretos ou sem filtro de área: inicia imediatamente
            params["_resolved_topic_ids"] = None
            self._open_progress_and_run(params)

    def _fetch_topics_then_dialog(self, terms: list, params: dict):
        """Busca os topics na API (em thread) e depois abre o diálogo de seleção."""
        loading = tk.Toplevel(self.root)
        loading.title("Buscando áreas…")
        loading.resizable(False, False)
        self._center_on_root(loading, 380, 120)
        ttk.Label(
            loading, text="Consultando o OpenAlex, aguarde…", style="Body.TLabel"
        ).pack(pady=(22, 10))
        bar = ttk.Progressbar(loading, mode="indeterminate")
        bar.pack(padx=28, fill=tk.X)
        bar.start(12)
        loading.update()

        def fetch():
            import requests
            results_by_term: dict[str, list] = {}
            for term in terms:
                try:
                    resp = requests.get(
                        f"{OPENALEX_BASE}/topics",
                        params={
                            "search": term,
                            "per_page": 10,
                            "mailto": openalex_colab.POLITE_EMAIL,
                        },
                        timeout=12,
                    )
                    results_by_term[term] = resp.json().get("results", []) if resp.ok else []
                except Exception:
                    results_by_term[term] = []
            self.root.after(
                0, lambda: self._on_topics_fetched(loading, results_by_term, params)
            )

        threading.Thread(target=fetch, daemon=True).start()

    def _on_topics_fetched(
        self, loading: tk.Toplevel, results_by_term: dict, params: dict
    ):
        loading.destroy()
        resolved_ids = self._show_topic_selection_dialog(results_by_term)
        if resolved_ids is None:
            return  # usuário cancelou
        params["_resolved_topic_ids"] = resolved_ids or None
        self._open_progress_and_run(params)

    def _show_topic_selection_dialog(self, results_by_term: dict) -> list | None:
        """
        Mostra um diálogo modal com todos os topics encontrados por termo.
        Todos ficam pré-marcados. O usuário pode desmarcar os que não quiser.
        Retorna lista de IDs selecionados, ou None se cancelado.
        """
        dialog = tk.Toplevel(self.root)
        dialog.title("Selecionar topics do OpenAlex")
        dialog.resizable(True, True)
        self._center_on_root(dialog, 760, 600)
        dialog.grab_set()   # modal

        result_holder: list[list | None] = [None]
        check_vars: list[tuple[tk.BooleanVar, str, str]] = []  # (var, id, nome)

        # Cabeçalho
        head = ttk.Frame(dialog, padding=(20, 16, 20, 8))
        head.pack(fill=tk.X)
        ttk.Label(head, text="Confirme os subtopics da análise", style="Section.TLabel").pack(anchor=tk.W)
        ttk.Label(
            head, text="Todos estão pré-selecionados. Desmarque os que não quiser usar.", style="Hint.TLabel",
        ).pack(anchor=tk.W, pady=(2, 0))

        # Botões (empacotados antes da área rolável para ficarem sempre visíveis)
        btn_row = ttk.Frame(dialog, padding=(20, 12))
        btn_row.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Separator(dialog, orient="horizontal").pack(side=tk.BOTTOM, fill=tk.X)

        # Área scrollável
        outer = ttk.Frame(dialog, padding=(12, 0))
        outer.pack(fill=tk.BOTH, expand=True)

        cvs = self._themed_widget(tk.Canvas(outer, highlightthickness=0, bd=0), "canvas")
        cvs.configure(bg=self.pal["bg"])
        vsb = ttk.Scrollbar(outer, orient="vertical", command=cvs.yview)
        inner = ttk.Frame(cvs, padding=(8, 0))
        inner.bind(
            "<Configure>",
            lambda e: cvs.configure(scrollregion=cvs.bbox("all")),
        )
        inner_window = cvs.create_window((0, 0), window=inner, anchor="nw")
        cvs.bind("<Configure>", lambda e: cvs.itemconfig(inner_window, width=e.width))
        cvs.configure(yscrollcommand=vsb.set)
        cvs.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Scroll do mouse só ligado enquanto o cursor está sobre este canvas,
        # e desligado ao fechar o diálogo — bind_all sem unbind_all fazia o
        # binding sobreviver à destruição do canvas e disparar
        # "_tkinter.TclError: invalid command name" a cada scroll depois.
        cvs.bind(
            "<Enter>",
            lambda e: cvs.bind_all(
                "<MouseWheel>",
                lambda ev: cvs.yview_scroll(-1 * (ev.delta // 120), "units"),
            ),
        )
        cvs.bind("<Leave>", lambda e: cvs.unbind_all("<MouseWheel>"))
        dialog.bind("<Destroy>", lambda e: cvs.unbind_all("<MouseWheel>"))

        # Popula topics por termo de busca: um cartão por termo
        for term, results in results_by_term.items():
            card = ttk.Frame(inner, style="Card.TFrame", padding=(16, 12))
            card.pack(fill=tk.X, pady=6)
            ttk.Label(card, text=f'Área buscada: "{term}"', style="Selected.TLabel").pack(
                anchor=tk.W, pady=(0, 6)
            )

            if not results:
                ttk.Label(card, text="Nenhum topic encontrado para este termo.", style="Hint.TLabel").pack(
                    anchor=tk.W
                )
                continue

            for r in results:
                var = tk.BooleanVar(value=True)  # pré-marcado
                tid  = r["id"]
                name = r["display_name"]
                subfield = r.get("subfield", {}).get("display_name", "?")
                field    = r.get("field",    {}).get("display_name", "?")
                domain   = r.get("domain",   {}).get("display_name", "?")
                works    = r.get("works_count", 0)

                check_vars.append((var, tid, name))

                ttk.Checkbutton(card, text=name, variable=var).pack(anchor=tk.W, pady=(6, 0))
                ttk.Label(
                    card,
                    text=f"{domain} › {field} › {subfield}   ·   {works:,} publicações".replace(",", "."),
                    style="Hint.TLabel",
                ).pack(anchor=tk.W, padx=(28, 0))

        def on_ok():
            result_holder[0] = [tid for var, tid, _ in check_vars if var.get()]
            dialog.destroy()

        def on_cancel():
            dialog.destroy()  # result_holder permanece None

        ttk.Button(
            btn_row, text="Confirmar e executar", style="Accent.TButton", command=on_ok
        ).pack(side=tk.RIGHT)
        ttk.Button(btn_row, text="Cancelar", command=on_cancel).pack(side=tk.RIGHT, padx=8)
        ttk.Button(
            btn_row,
            text="Marcar tudo",
            command=lambda: [v.set(True) for v, _, _ in check_vars],
        ).pack(side=tk.LEFT)
        ttk.Button(
            btn_row,
            text="Desmarcar tudo",
            command=lambda: [v.set(False) for v, _, _ in check_vars],
        ).pack(side=tk.LEFT, padx=8)

        dialog.wait_window()
        return result_holder[0]

    def _open_progress_and_run(self, params: dict):
        """Abre a janela de progresso e inicia a thread de análise."""
        pw = tk.Toplevel(self.root)
        pw.title("Executando análise")
        self._center_on_root(pw, 760, 580)

        body = ttk.Frame(pw, padding=(22, 18, 22, 12))
        body.pack(fill=tk.BOTH, expand=True)

        status = {
            "title": ttk.Label(body, text="Processando…", style="Section.TLabel"),
            "step": ttk.Label(body, text="Preparando", style="Status.TLabel"),
            "bar": ttk.Progressbar(body, mode="indeterminate"),
        }
        status["title"].pack(anchor=tk.W)
        status["step"].pack(anchor=tk.W, pady=(2, 10))
        status["bar"].pack(fill=tk.X)
        status["bar"].start(12)

        status["log_label"] = ttk.Label(body, text="Log detalhado", style="Hint.TLabel")
        status["log_label"].pack(anchor=tk.W, pady=(16, 4))
        tf = ttk.Frame(body)
        tf.pack(fill=tk.BOTH, expand=True)
        txt = self._themed_widget(
            tk.Text(tf, height=18, wrap=tk.WORD, font=self.f_mono, relief="flat", bd=0,
                    padx=12, pady=10, state=tk.DISABLED),
            "console",
        )
        scr = ttk.Scrollbar(tf, command=txt.yview)
        txt.configure(yscrollcommand=scr.set)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._repaint_tk_widgets()

        # Área de ações exibida ao terminar (abrir grafos, pasta, fechar)
        status["actions"] = ttk.Frame(body)
        pw.update()

        threading.Thread(
            target=self._analysis_thread,
            args=(params, txt, pw, status),
            daemon=True,
        ).start()

    # Linhas do log que indicam em que etapa a análise está
    _STEP_PATTERNS = [
        (re.compile(r"^Encontrados \d+ pesquisadores"), "Pesquisadores encontrados — coletando publicações"),
        (re.compile(r"MÉTRICAS DESCRITIVAS"), "Calculando métricas da rede de pesquisadores"),
        (re.compile(r"^Rede grande"), "Calculando intermediação (rede grande — pode levar até 1 minuto)"),
        (re.compile(r"^Gráficos salvos"), "Exportando planilhas"),
        (re.compile(r"^Grafo de instituições"), "Montando a rede entre instituições"),
    ]
    _PROGRESS_RE = re.compile(r"^\[(\d+)/(\d+)\]")

    def _on_log_line(self, line: str, status: dict):
        """Atualiza a barra e o texto de etapa a partir das linhas do log."""
        try:
            m = self._PROGRESS_RE.match(line)
            if m:
                i, n = int(m.group(1)), int(m.group(2))
                bar = status["bar"]
                if str(bar.cget("mode")) != "determinate":
                    bar.stop()
                    bar.configure(mode="determinate", maximum=n)
                bar.configure(value=i)
                status["step"].configure(text=f"Coletando publicações — pesquisador {i} de {n}")
                return
            for pattern, text in self._STEP_PATTERNS:
                if pattern.search(line):
                    status["step"].configure(text=text)
                    return
        except tk.TclError:
            pass  # janela de progresso já fechada

    def _finish_progress(self, pw: tk.Toplevel, status: dict, ok: bool, message: str, prefix: str = ""):
        try:
            bar = status["bar"]
            bar.stop()
            bar.configure(mode="determinate", maximum=1, value=1 if ok else 0)
            status["title"].configure(
                text="Análise concluída" if ok else "A análise falhou",
                style="Success.TLabel" if ok else "Danger.TLabel",
            )
            status["step"].configure(text=message)
            pw.title("Análise concluída" if ok else "Erro na análise")

            actions = status["actions"]
            actions.pack(fill=tk.X, pady=(14, 0), before=status["log_label"])
            ttk.Button(actions, text="Fechar", command=pw.destroy).pack(side=tk.RIGHT)
            if ok:
                for suffix, label in ((".html", "Grafo de pesquisadores"),
                                      ("_instituicoes.html", "Rede entre instituições")):
                    path = Path(f"{prefix}{suffix}")
                    if path.exists():
                        ttk.Button(actions, text=f"Abrir {label.lower()}", style="Accent.TButton",
                                   command=lambda p=path: self._open_path(p)).pack(side=tk.LEFT, padx=(0, 8))
                ttk.Button(actions, text="Abrir pasta", command=self._open_results).pack(side=tk.LEFT)
        except tk.TclError:
            pass  # usuário fechou a janela de progresso antes de terminar

    def _analysis_thread(self, params: dict, log: tk.Text, pw: tk.Toplevel, status: dict):
        old_out, old_err = sys.stdout, sys.stderr
        redir = TextRedirector(log, on_line=lambda line: self._on_log_line(line, status))
        sys.stdout = sys.stderr = redir

        try:
            prefix = str(self.results_dir / params["output"])

            # Aplica o email do usuário ao módulo para o polite pool do OpenAlex
            if params.get("email"):
                openalex_colab.POLITE_EMAIL = params["email"]

            # 1. Instituição
            if params["institution_id"]:
                inst_id   = params["institution_id"]
                inst_name = params["institution"]
                print(f"Usando instituição selecionada: {inst_name}\n  ID: {inst_id}\n")
            else:
                inst_id, inst_name = openalex_colab.find_institution(
                    params["institution"], interactive=False
                )

            # 2. Áreas de conhecimento
            topic_ids  = None
            concept_id = None

            if params.get("_resolved_topic_ids") is not None:
                # IDs já resolvidos pelo diálogo de seleção (podem ser lista vazia
                # se o usuário desmarcou tudo — nesse caso filtra sem área)
                topic_ids = params["_resolved_topic_ids"] or None
                if topic_ids:
                    print(f"Usando {len(topic_ids)} topic(s) selecionado(s) pelo usuário.\n")
                else:
                    print("Nenhum topic selecionado — buscando sem filtro de área.\n")

            elif params["topic_id"]:
                raw = [t.strip() for t in params["topic_id"].split(",") if t.strip()]
                topic_ids = [
                    t if t.startswith("http") else f"https://openalex.org/{t}"
                    for t in raw
                ]
                print(f"Usando {len(topic_ids)} topic(s) por ID: {', '.join(raw)}\n")

            # 3. Pesquisadores
            self.root.after(0, lambda: status["step"].configure(text="Buscando pesquisadores da instituição"))
            authors = openalex_colab.get_authors_by_institution(
                inst_id,
                max_authors=params["max_authors"],
                topic_ids=topic_ids,
                concept_id=concept_id,
            )
            if not authors:
                print("Nenhum pesquisador encontrado. Verifique os filtros.")
                self.root.after(0, lambda: self._finish_progress(
                    pw, status, False,
                    "Nenhum pesquisador encontrado. Confira o nome da universidade, "
                    "tente sem filtro de área ou com um período mais amplo.",
                ))
                return

            author_ids   = [a["id"] for a in authors]
            author_names = {a["id"]: a["name"] for a in authors}

            # 4. Coautorias
            year_from = int(params["year_from"]) if params["year_from"] else None
            year_to   = int(params["year_to"])   if params["year_to"]   else None

            edges, coauthor_names, works_by_year, works_institutions = openalex_colab.get_coauthorships(
                author_ids,
                max_works_per_author=params["max_works"],
                topic_ids=topic_ids,
                concept_id=concept_id,
                year_from=year_from,
                year_to=year_to,
                max_authors_per_work=params["max_authors_per_work"],
            )
            author_names.update(coauthor_names)

            # 5. Grafo
            G = openalex_colab.build_graph(
                edges, author_names, author_ids,
                restrict_to_institution=params["restrict"],
            )

            # 6. Métricas + exportação (HTML, GEXF, PNGs e CSVs)
            metrics = openalex_colab.compute_metrics(G)
            self.root.after(0, lambda: status["step"].configure(text="Gerando grafo interativo e gráficos"))
            openalex_colab.export_graph(G, output_prefix=prefix)
            openalex_colab.generate_charts(G, metrics, authors, works_by_year, output_prefix=prefix)
            openalex_colab.export_csvs(G, authors, metrics, works_by_year, output_prefix=prefix)

            # 7. Rede de colaboração entre instituições
            G_inst = openalex_colab.build_institution_graph(
                works_institutions, inst_id, max_institutions=params["max_institutions"]
            )
            inst_metrics = openalex_colab.compute_institution_metrics(G_inst, inst_id)
            openalex_colab.export_institution_outputs(G_inst, inst_metrics, output_prefix=prefix)

            print(f"\n✓ Concluído! Arquivos salvos em:\n  {self.results_dir}")
            self._collect_output_files(params["output"])
            summary = (
                f"{G.number_of_nodes()} pesquisadores · {G.number_of_edges()} colaborações · "
                f"{G_inst.number_of_nodes()} instituições — {len(self.output_files)} arquivos gerados"
            )
            self.root.after(0, lambda: self._finish_progress(pw, status, True, summary, prefix))

        except Exception:
            detail = traceback.format_exc()
            print(f"\n✗ Erro:\n{detail}")
            last = detail.strip().splitlines()[-1]
            self.root.after(0, lambda: self._finish_progress(pw, status, False, last))

        finally:
            sys.stdout, sys.stderr = old_out, old_err

    # ----------------------------------------------------------
    # Utilitários
    # ----------------------------------------------------------

    def _collect_output_files(self, prefix: str):
        self.output_files = []
        exts = [
            ".html", ".gexf",
            "_pesquisadores.csv", "_colaboracoes.csv", "_comunidades.csv",
            "_publicacoes_por_ano.csv", "_resumo_metricas.csv",
            "_distribuicao_grau.png", "_top_centralidade_grau.png",
            "_top_intermediacao.png", "_tamanho_comunidades.png",
            "_publicacoes_por_ano.png", "_produtividade_vs_centralidade.png",
            "_instituicoes.html", "_instituicoes.gexf", "_instituicoes.csv",
            "_colaboracoes_instituicoes.csv", "_top_instituicoes_parceiras.png",
        ]
        for ext in exts:
            p = self.results_dir / f"{prefix}{ext}"
            if p.exists():
                self.output_files.append(str(p))

    def _open_path(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir:\n{path}\n\n{e}")

    def _open_results(self):
        self._open_path(self.results_dir)

    def _help(self):
        hw = tk.Toplevel(self.root)
        hw.title("Ajuda — Como usar")
        self._center_on_root(hw, 760, 680)

        frame = ttk.Frame(hw, padding=(20, 16))
        frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frame, text="Como usar o SciCollab-BR", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))

        tf = ttk.Frame(frame)
        tf.pack(fill=tk.BOTH, expand=True)
        txt = self._themed_widget(
            tk.Text(tf, wrap=tk.WORD, font=self.f_body, relief="flat", bd=0, padx=16, pady=12,
                    spacing1=2, spacing3=2),
            "text",
        )
        scr = ttk.Scrollbar(tf, command=txt.yview)
        txt.configure(yscrollcommand=scr.set)
        scr.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)
        txt.tag_configure("h", font=self.f_bold, spacing1=12, foreground=self.pal["accent"])
        self._repaint_tk_widgets()

        sections = [
            ("1. Universidade (obrigatório)",
             "Digite o nome e pressione Enter (ou clique em Buscar). Clique no resultado certo — "
             "a universidade selecionada aparece destacada logo abaixo."),
            ("2. Área de conhecimento (opcional)",
             "Filtra por faculdade/área de pesquisa dentro da universidade.\n"
             "• Pela lista: clique nas áreas desejadas (clique de novo para desmarcar).\n"
             "• Digitando: separe várias com ponto e vírgula, ex: Computer Science; Information Systems\n"
             "• Topic IDs: cole IDs diretos do OpenAlex (ex: T10712,T14330) — têm prioridade.\n"
             "Deixe tudo em branco para analisar a universidade inteira."),
            ("3. Período (opcional)", "Filtra as publicações por ano. Ex: 2018 até 2024."),
            ("4. Limites",
             "• Máx. pesquisadores: quantos autores buscar (padrão 100).\n"
             "• Máx. publicações por pesquisador: obras a verificar (padrão 50).\n"
             "• Máx. instituições: quantas mostrar na rede entre universidades (padrão 100).\n"
             "• Ignorar publicações com mais de N autores: exclui autoria em massa, que deixa o "
             "grafo ilegível (padrão 50; 0 = todas).\n"
             "Valores maiores = análise mais completa, porém mais lenta."),
            ("5. Opções",
             "• Só colaborações internas: mantém só vínculos entre pesquisadores da universidade.\n"
             "• Nome dos arquivos: prefixo usado nos resultados.\n"
             "• E-mail: recomendado, reduz bloqueios temporários do OpenAlex."),
            ("Arquivos gerados (pasta \"resultados\")",
             "• .html — grafo de pesquisadores (abra no navegador)\n"
             "• _instituicoes.html — rede de colaboração entre instituições\n"
             "• .gexf — para o Gephi (análise avançada)\n"
             "• Planilhas: _pesquisadores, _colaboracoes, _comunidades, _publicacoes_por_ano, "
             "_resumo_metricas, _instituicoes, _colaboracoes_instituicoes (.csv)\n"
             "• 7 gráficos .png"),
        ]
        for title, body in sections:
            txt.insert(tk.END, title + "\n", "h")
            txt.insert(tk.END, body + "\n")
        txt.config(state=tk.DISABLED)

        ttk.Button(frame, text="Fechar", command=hw.destroy).pack(anchor=tk.E, pady=(12, 0))


# ------------------------------------------------------------
# Entrada
# ------------------------------------------------------------

def main():
    _enable_windows_dpi_awareness()
    root = tk.Tk()
    if not DependencyInstaller.check_and_install(root):
        root.destroy()
        sys.exit(1)
    OpenAlexGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
